import logging
from uuid import UUID

import grpc

from dataclay.metadata.api import MetadataAPI
from dataclay.proto.backend import backend_pb2_grpc
from dataclay.proto.metadata import metadata_pb2_grpc

BACKEND_METHODS = [
    "RegisterObjects",
    "MakePersistent",
    "CallActiveMethod",
    "GetObjectProperties",
    "UpdateObjectProperties",
    "NewObjectVersion",
    "ConsolidateObjectVersion",
    "ProxifyObject",
    "ChangeObjectId",
    "SendObjects",
    "FlushAll",
    "Stop",
    "Drain",
    "NewObjectReplica",
]

METADATA_METHODS = [
    "NewAccount",
    "NewSession",
    "NewDataset",
    "CloseSession",
    "GetDataclay",
    "GetAllBackends",
    "GetAllObjects",
    "GetObjectMDById",
    "GetObjectMDByAlias",
    "NewAlias",
    "GetAllAlias",
    "DeleteAlias",
    "Stop",
]

logger = logging.getLogger(__name__)


class BackendMeta(type):
    def __init__(cls, name, bases, dct):
        for method_name in BACKEND_METHODS:

            def dynamic_method(self, request, context):
                for mid in self.middleware:
                    mid(method_name, request, context)
                    logger.info("Ready to proxy method %s", method_name)
                stub = self._get_stub(context)
                method_to_call = getattr(stub, method_name)
                return method_to_call(request)

            setattr(cls, method_name, dynamic_method)

        super().__init__(name, bases, dct)


class MetadataMeta(type):
    def __init__(cls, name, bases, dct):
        for method_name in METADATA_METHODS:

            def dynamic_method(self, request, context):
                for mid in self.middleware:
                    mid(method_name, request, context)
                    logger.info("Ready to proxy method %s", method_name)

                method_to_call = getattr(self.stub, method_name)
                return method_to_call(request)

            setattr(cls, method_name, dynamic_method)

        super().__init__(name, bases, dct)


class BackendProxyBase(backend_pb2_grpc.BackendServiceServicer, metaclass=BackendMeta):
    metadata_client: MetadataAPI
    backend_stubs: dict[UUID, backend_pb2_grpc.BackendServiceStub]
    middleware: list

    def _refresh_backends(self):
        for k, v in self.metadata_client.get_all_backends().items():
            # TODO: Something something SSL check (maybe not always will be an insecure channel)
            ch = grpc.insecure_channel(f"{v.host}:{v.port}")
            self.backend_stubs[k] = backend_pb2_grpc.BackendServiceStub(ch)

    def _get_stub(self, context):
        """Get a channel to a specific backend.

        Metadata header (retrieved through the context) *must* contain the
        backend-id key.
        """
        metadata = context.invocation_metadata()

        for key, value in metadata:
            if key == "backend-id":
                backend_id = UUID(value)
                break
        else:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT, "backend-id metadata header *must* be set"
            )

        try:
            return self.backend_stubs[backend_id]
        except KeyError:
            pass

        self._refresh_backends()
        try:
            return self.backend_stubs[backend_id]
        except KeyError:
            context.abort(grpc.StatusCode.NOT_FOUND, "Backend %s does not exist" % backend_id)


class MetadataProxyBase(metadata_pb2_grpc.MetadataServiceServicer, metaclass=MetadataMeta):
    pass
