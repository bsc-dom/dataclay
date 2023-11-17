"""Proxy server, with pluggable middleware."""

import logging
import threading
from uuid import UUID
from concurrent import futures

import grpc

from dataclay.config import settings
from dataclay.proto.backend import backend_pb2_grpc
from dataclay.proto.metadata import metadata_pb2_grpc
from dataclay.metadata.api import MetadataAPI

logger = logging.getLogger(__name__)


def serve():
    stop_event = threading.Event()

    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=settings.thread_pool_workers),
        options=[("grpc.max_send_message_length", -1), ("grpc.max_receive_message_length", -1)],
    )
    
    md_api = MetadataAPI(settings.kv_host, settings.kv_port)

    backend_pb2_grpc.add_BackendServiceServicer_to_server(
        BackendProxyServicer(md_api), server
    )
    metadata_pb2_grpc.add_MetadataServiceServicer_to_server(
        MetadataProxyServicer(), server
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
    interceptors: list[grpc.UnaryUnaryClientInterceptor]

    def __init__(self, metadata_client, *interceptors):
        self.backend_stubs = dict()
        self.metadata_client = metadata_client
        self.interceptors = interceptors

    def _refresh_backends(self):
        for k, v in self.metadata_client.get_all_backends().items():
            # TODO: Something something SSL check (maybe not always will be an insecure channel)
            ch = grpc.insecure_channel(f'{v.host}:{v.port}')
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
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "backend-id metadata header *must* be set")
        
        try:
            return self.backend_stubs[backend_id]
        except KeyError:
            pass

        self._refresh_backends()
        try:
            return self.backend_stubs[backend_id]
        except KeyError:
            context.abort(grpc.StatusCode.NOT_FOUND, "Backend %s does not exist" % backend_id)

    def RegisterObjects(self, request, context):
        stub = self._get_stub(context)
        return stub.RegisterObjects(request)


class MetadataProxyServicer(metadata_pb2_grpc.MetadataServiceServicer):
    pass