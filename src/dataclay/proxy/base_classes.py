import asyncio
import logging
from uuid import UUID

import grpc
from google.protobuf.empty_pb2 import Empty

from dataclay.metadata.api import MetadataAPI
from dataclay.proto.backend import backend_pb2_grpc
from dataclay.proto.metadata import metadata_pb2_grpc

from .exceptions import MiddlewareException

BACKEND_METHODS = [
    "RegisterObjects",
    "MakePersistent",
    "CallActiveMethod",
    "GetObjectAttribute",
    "SetObjectAttribute",
    "DelObjectAttribute",
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
    "NewDataset",
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


class MiddlewareBase:
    """Base class to be used for middlewares.

    To implement a middleware, create a new class by deriving this
    MiddlewareBase and implement the methods that you need.
    """

    def __call__(self, method_name, request, context):
        try:
            m = getattr(self, method_name)
        except AttributeError:
            return
        logger.debug("Middleware %r is processing method %s" % (self, method_name))
        m(request, context)


class BackendMeta(type):
    def __init__(cls, name, bases, dct):
        for method_name in BACKEND_METHODS:

            def dynamic_method(self, request, context, *, method_name=method_name):
                logger.info("Ready to proxy backend method %s", method_name)
                try:
                    # Note to future readers:
                    # The method_name variable from the loop cannot be directly used here, as it is
                    # bound through the scope. You need to bound it to a local variable (hence the
                    # method_name with a default value).
                    for mid in self.middleware:
                        mid(method_name, request, context)
                except MiddlewareException as e:
                    context.set_details(str(e))
                    context.set_code(e.status_code or grpc.StatusCode.PERMISSION_DENIED)
                    logger.info("Middleware %r has blocked method %s" % (mid, method_name))
                    return Empty()
                else:
                    stub = asyncio.run(self._get_stub(context))
                    method_to_call = getattr(stub, method_name)
                    return method_to_call(request)

            setattr(cls, method_name, dynamic_method)
        super().__init__(name, bases, dct)


class MetadataMeta(type):
    def __init__(cls, name, bases, dct):
        for method_name in METADATA_METHODS:

            def dynamic_method(self, request, context, *, method_name=method_name):
                logger.info("Ready to proxy metadata method %s", method_name)
                try:
                    # Note to future readers:
                    # The method_name variable from the loop cannot be directly used here, as it is
                    # bound through the scope. You need to bound it to a local variable (hence the
                    # method_name with a default value).
                    for mid in self.middleware:
                        mid(method_name, request, context)
                except MiddlewareException as e:
                    context.set_details(str(e))
                    context.set_code(e.status_code or grpc.StatusCode.PERMISSION_DENIED)
                    logger.info("Middleware %r has blocked method %s" % (mid, method_name))
                    return Empty()
                else:
                    method_to_call = getattr(self.stub, method_name)
                    return method_to_call(request)

            setattr(cls, method_name, dynamic_method)
        super().__init__(name, bases, dct)


class BackendProxyBase(backend_pb2_grpc.BackendServiceServicer, metaclass=BackendMeta):
    metadata_client: MetadataAPI
    backend_stubs: dict[UUID, backend_pb2_grpc.BackendServiceStub]
    middleware: list

    async def _refresh_backends(self):
        for k, v in (await self.metadata_client.get_all_backends()).items():
            # TODO: Something something SSL check (maybe not always will be an insecure channel)
            ch = grpc.insecure_channel(f"{v.host}:{v.port}")
            self.backend_stubs[k] = backend_pb2_grpc.BackendServiceStub(ch)

    async def _get_stub(self, context):
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

        await self._refresh_backends()
        try:
            return self.backend_stubs[backend_id]
        except KeyError:
            context.abort(grpc.StatusCode.NOT_FOUND, "Backend %s does not exist" % backend_id)


class MetadataProxyBase(metadata_pb2_grpc.MetadataServiceServicer, metaclass=MetadataMeta):
    pass
