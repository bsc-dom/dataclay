from __future__ import annotations

import logging
import signal
import threading
import time
import traceback
from concurrent import futures
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import grpc
from google.protobuf.empty_pb2 import Empty
from grpc_health.v1 import health, health_pb2, health_pb2_grpc

from dataclay.config import settings
from dataclay.exceptions.exceptions import AlreadyExistError
from dataclay.metadata.api import MetadataAPI
from dataclay.metadata.kvdata import Backend
from dataclay.proto.common import common_pb2
from dataclay.proto.metadata import metadata_pb2, metadata_pb2_grpc
from dataclay.utils.backend_clients import BackendClientsManager
from dataclay.utils.uuid import str_to_uuid

logger = logging.getLogger(__name__)


def serve():
    stop_event = threading.Event()

    logger.info("Starting MetadataService")
    metadata_api = MetadataAPI(settings.kv_host, settings.kv_port)

    if not metadata_api.is_ready(timeout=10):
        raise RuntimeError("KV store is not ready. Aborting!")

    # Try to set the dataclay id if don't exists yet
    try:
        if settings.dataclay_id is None:
            settings.dataclay_id = uuid4()

        metadata_api.new_dataclay(
            settings.dataclay_id,
            settings.metadata.host,
            settings.metadata.port,
            is_this=True,
        )
    except AlreadyExistError:
        logger.info("MetadataService already registered with id %s", settings.dataclay_id)
        settings.dataclay_id = metadata_api.get_dataclay("this").id
    else:
        metadata_api.new_superuser(
            settings.root_username, settings.root_password, settings.root_dataset
        )

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=settings.thread_pool_max_workers))
    metadata_pb2_grpc.add_MetadataServiceServicer_to_server(
        MetadataServicer(metadata_api, stop_event), server
    )

    if settings.metadata.enable_healthcheck:
        logger.info("Enabling healthcheck for MetadataService")
        health_servicer = health.HealthServicer(
            experimental_non_blocking=True,
            experimental_thread_pool=futures.ThreadPoolExecutor(
                max_workers=settings.healthcheck_max_workers
            ),
        )
        health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)
        health_servicer.set(
            "dataclay.proto.metadata.MetadataService", health_pb2.HealthCheckResponse.SERVING
        )

    address = f"{settings.metadata.listen_address}:{settings.metadata.port}"
    server.add_insecure_port(address)
    server.start()
    logger.info("MetadataService listening on %s", address)

    # Set signal hook for SIGINT and SIGTERM
    signal.signal(signal.SIGINT, lambda sig, frame: stop_event.set())
    signal.signal(signal.SIGTERM, lambda sig, frame: stop_event.set())

    # Wait until stop_event is set. Then, gracefully stop dataclay metadata service.
    stop_event.wait()
    logger.info("Stopping MetadataService")

    server.stop(5)


class MetadataServicer(metadata_pb2_grpc.MetadataServiceServicer):
    """Provides methods that implement functionality of metadata server"""

    def __init__(self, metadata_api: MetadataAPI, stop_event: threading.Event):
        self.metadata_api = metadata_api
        self.stop_event = stop_event

        # Start the backend clients manager
        self.backend_clients = BackendClientsManager(metadata_api)
        self.backend_clients.start_update()
        self.backend_clients.start_subscribe()

    # TODO: define get_exception_info(..) to serialize excpetions

    def NewAccount(self, request, context):
        try:
            self.metadata_api.new_account(request.username, request.password)
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()
        return Empty()

    def NewDataset(self, request, context):
        try:
            self.metadata_api.new_dataset(request.username, request.password, request.dataset)
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()
        return Empty()

    def GetDataclay(self, request, context):
        try:
            dataclay = self.metadata_api.get_dataclay(UUID(request.dataclay_id))
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return common_pb2.Dataclay()
        return dataclay.get_proto()

    def GetAllBackends(self, request, context):
        try:
            response = {}
            if request.force:
                backends = self.metadata_api.get_all_backends(request.from_backend)
                for id, backend in backends.items():
                    response[str(id)] = backend.get_proto()
            else:
                # Using a cached version of the backends to avoid querying the KV store for each client request
                for id, backend_client in self.backend_clients.items():
                    backend = Backend(
                        id=id,
                        host=backend_client.host,
                        port=backend_client.port,
                        dataclay_id=id,  # wrong: to change or remove completely
                    )
                    response[str(id)] = backend.get_proto()
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return metadata_pb2.GetAllBackendsResponse()
        return metadata_pb2.GetAllBackendsResponse(backends=response)

    ###################
    # Object Metadata #
    ###################

    def GetAllObjects(self, request, context):
        try:
            object_mds = self.metadata_api.get_all_objects()
            response = {}
            for id, object_md in object_mds.items():
                response[str(id)] = object_md.get_proto()
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return metadata_pb2.GetAllObjectsResponse()
        return metadata_pb2.GetAllObjectsResponse(objects=response)

    def GetObjectMDById(self, request, context):
        try:
            object_md = self.metadata_api.get_object_md_by_id(UUID(request.object_id))
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return common_pb2.ObjectMetadata()
        return object_md.get_proto()

    def GetObjectMDByAlias(self, request, context):
        try:
            object_md = self.metadata_api.get_object_md_by_alias(
                request.alias_name, request.dataset_name
            )
        except Exception as e:
            traceback.print_exc()
            context.abort(grpc.StatusCode.INTERNAL, str(e))
        return object_md.get_proto()

    #########
    # Alias #
    #########

    def NewAlias(self, request, context):
        try:
            self.metadata_api.new_alias(
                request.alias_name, request.dataset_name, UUID(request.object_id)
            )
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()
        return Empty()

    def GetAllAlias(self, request, context):
        try:
            aliases = self.metadata_api.get_all_alias(
                request.dataset_name, str_to_uuid(request.object_id)
            )
            response = {}
            for alias_name, alias in aliases.items():
                response[alias_name] = alias.get_proto()
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return metadata_pb2.GetAllAliasResponse()
        return metadata_pb2.GetAllAliasResponse(aliases=response)

    def DeleteAlias(self, request, context):
        try:
            self.metadata_api.delete_alias(request.alias_name, request.dataset_name)
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()
        return Empty()

    def Stop(self, request, context):
        try:
            self.stop_event.set()
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
        return Empty()
