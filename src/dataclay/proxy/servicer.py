"""Proxy server, with pluggable middleware."""

import logging
import threading
from concurrent import futures

import grpc

from dataclay.config import settings
from dataclay.metadata.api import MetadataAPI
from dataclay.proto.backend import backend_pb2_grpc
from dataclay.proto.metadata import metadata_pb2_grpc


from .base_classes import BackendProxyBase, MetadataProxyBase

logger = logging.getLogger(__name__)

global_metadata_api = None


def serve(
    md_api: MetadataAPI,
    interceptors: list[grpc.ServerInterceptor],
    middleware_metadata: list,
    middleware_backend: list,
):
    global global_metadata_api 
    global_metadata_api = md_api
    
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


class BackendProxyServicer(BackendProxyBase):
    def __init__(self, metadata_client, *middleware):
        self.backend_stubs = dict()
        self.metadata_client = metadata_client
        self.middleware = middleware


class MetadataProxyServicer(MetadataProxyBase):
    def __init__(self, stub, *middleware):
        self.middleware = middleware
        self.stub = stub
