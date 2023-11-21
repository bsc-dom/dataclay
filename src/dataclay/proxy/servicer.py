"""Proxy server, with pluggable middleware."""

import logging
import threading
from concurrent import futures
from functools import wraps
from uuid import UUID

import grpc

from dataclay.config import settings
from dataclay.metadata.api import MetadataAPI
from dataclay.proto.backend import backend_pb2_grpc
from dataclay.proto.metadata import metadata_pb2_grpc

logger = logging.getLogger(__name__)


def apply_middleware(f):
    """Decorator for methods in the proxy classes.

    This can be applied to methods of both classes BackendProxyServicer and
    MetadataProxyServicer classes. Note that this decorator relies on two
    specific idiosincrasies:
    - The method name matches the gRPC method.
    - The class has a middleware attribute (list of middleware to apply).
    """

    @wraps(f)
    def wrapper(self, request, context):
        logger.debug("Entrypoint for method %s", f.__name__)
        for mid in self.middleware:
            mid(f.__name__, request, context)
        logger.info("Ready to proxy method %s", f.__name__)
        return f(self, request, context)

    return wrapper


def serve(
    md_api: MetadataAPI,
    interceptors: list[grpc.ServerInterceptor],
    middleware_metadata: list,
    middleware_backend: list,
):
    stop_event = threading.Event()

    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=settings.thread_pool_max_workers),
        options=[("grpc.max_send_message_length", -1), ("grpc.max_receive_message_length", -1)],
        interceptors=interceptors,
    )

    backend_pb2_grpc.add_BackendServiceServicer_to_server(
        BackendProxyServicer(md_api, *middleware_backend), server
    )

    # TODO: Something something SSL check (maybe not always will be an insecure channel)
    ch = grpc.insecure_channel(f"{settings.proxy.mds_host}:{settings.proxy.mds_port}")
    mds_stub = metadata_pb2_grpc.MetadataServiceStub(ch)
    metadata_pb2_grpc.add_MetadataServiceServicer_to_server(
        MetadataProxyServicer(mds_stub, *middleware_metadata), server
    )

    address = f"{settings.proxy.listen_address}:{settings.proxy.port}"
    server.add_insecure_port(address)
    server.start()
    logger.info("Proxy service listening on %s", address)

    # Wait until stop_event is set. Then, gracefully stop dataclay backend.
    stop_event.wait()
    logger.info("Stopping proxy service")

    server.stop(5)
    grpc.insecure_channel


class BackendProxyServicer(backend_pb2_grpc.BackendServiceServicer):
    metadata_client: MetadataAPI
    backend_stubs: dict[UUID, backend_pb2_grpc.BackendServiceStub]
    middleware: list

    def __init__(self, metadata_client, *middleware):
        self.backend_stubs = dict()
        self.metadata_client = metadata_client
        self.middleware = middleware

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

    @apply_middleware
    def RegisterObjects(self, request, context):
        stub = self._get_stub(context)
        return stub.RegisterObjects(request)

    @apply_middleware
    def MakePersistent(self, request, context):
        stub = self._get_stub(context)
        return stub.MakePersistent(request)

    @apply_middleware
    def CallActiveMethod(self, request, context):
        stub = self._get_stub(context)
        return stub.CallActiveMethod(request)


class MetadataProxyServicer(metadata_pb2_grpc.MetadataServiceServicer):
    middleware: list
    # stub: Stub??
    def __init__(self, stub, *middleware):
        self.middleware = middleware
        self.stub = stub

    @apply_middleware
    def NewSession(self, request, context):
        return self.stub.NewSession(request)

    @apply_middleware
    def GetAllBackends(self, request, context):
        return self.stub.GetAllBackends(request)
