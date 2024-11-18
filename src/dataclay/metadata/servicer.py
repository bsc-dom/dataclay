from __future__ import annotations

import asyncio
import logging
import signal
from concurrent import futures
from functools import wraps
from uuid import UUID, uuid4

import grpc
from google.protobuf.empty_pb2 import Empty
from grpc_health.v1 import health, health_pb2, health_pb2_grpc

from dataclay.config import settings
from dataclay.event_loop import get_dc_event_loop, set_dc_event_loop
from dataclay.exceptions import AlreadyExistError
from dataclay.metadata.api import MetadataAPI
from dataclay.metadata.kvdata import Backend
from dataclay.proto.common import common_pb2
from dataclay.proto.metadata import metadata_pb2, metadata_pb2_grpc
from dataclay.utils.backend_clients import BackendClientsManager
from dataclay.utils.uuid import str_to_uuid

logger = logging.getLogger(__name__)


async def serve():
    # TODO: Think about moving the dc_event_loop to another place, since
    # metadata don't need to import runtime, but has to define the event loop
    set_dc_event_loop(asyncio.get_running_loop())

    logger.info("Starting Metadata Service...")
    metadata_api = MetadataAPI(settings.kv_host, settings.kv_port)

    # Wait for the KV store to be ready
    if not await metadata_api.is_ready(timeout=10):
        raise RuntimeError("KV store is not ready. Aborting!")

    # Try to set the dataclay id if don't exists yet
    try:
        if settings.dataclay_id is None:
            settings.dataclay_id = uuid4()

        await metadata_api.new_dataclay(
            settings.dataclay_id,
            settings.metadata.host,
            settings.metadata.port,
            is_this=True,
        )
    except AlreadyExistError:
        logger.info("MetadataService already registered with id %s", settings.dataclay_id)
        settings.dataclay_id = (await metadata_api.get_dataclay("this")).id
    else:
        await metadata_api.new_superuser(
            settings.root_username, settings.root_password, settings.root_dataset
        )

    # Initialize the servicer
    server = grpc.aio.server()
    metadata_servicer = MetadataServicer(metadata_api, server)
    metadata_pb2_grpc.add_MetadataServiceServicer_to_server(metadata_servicer, server)

    # Enable healthcheck for the server
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

    # Start the server
    address = f"{settings.metadata.listen_address}:{settings.metadata.port}"
    server.add_insecure_port(address)
    await server.start()
    logger.info("MetadataService listening on %s", address)

    # Register signal handlers for graceful termination
    loop = get_dc_event_loop()
    for sig in [signal.SIGINT, signal.SIGTERM]:
        get_dc_event_loop().add_signal_handler(
            sig, lambda: loop.create_task(server.stop(settings.shutdown_grace_period))
        )

    # Wait for the server to stop
    logger.info("MetadataService started")
    await server.wait_for_termination()
    logger.info("MetadataService stopped")
    await metadata_servicer.backend_clients.stop()
    await metadata_api.close()


class ServicerMethod:
    def __init__(self, ret_factory):
        self.ret_factory = ret_factory

    def __call__(self, func):
        @wraps(func)
        async def wrapper(servicer, request, context):
            try:
                return await func(servicer, request, context)
            except Exception as e:
                context.set_details(str(e))
                context.set_code(grpc.StatusCode.INTERNAL)
                logger.info("Exception during gRPC call\n", exc_info=True)
                return self.ret_factory()

        return wrapper


class MetadataServicer(metadata_pb2_grpc.MetadataServiceServicer):
    """Provides methods that implement functionality of metadata server"""

    def __init__(self, metadata_api: MetadataAPI, server: grpc.aio.Server):
        self.metadata_api = metadata_api
        self.server = server

        # Start the backend clients manager
        self.backend_clients = BackendClientsManager(metadata_api)
        self.backend_clients.start_update_loop()
        self.backend_clients.start_subscribe()

    # TODO: define get_exception_info(..) to serialize excpetions

    @ServicerMethod(Empty)
    async def NewAccount(self, request, context):
        await self.metadata_api.new_account(request.username, request.password)
        return Empty()

    @ServicerMethod(Empty)
    async def NewDataset(self, request, context):
        await self.metadata_api.new_dataset(request.username, request.password, request.dataset)
        return Empty()

    @ServicerMethod(common_pb2.Dataclay)
    async def GetDataclay(self, request, context):
        dataclay = await self.metadata_api.get_dataclay(UUID(request.dataclay_id))
        return dataclay.get_proto()

    @ServicerMethod(metadata_pb2.GetAllBackendsResponse)
    async def GetAllBackends(self, request, context):
        response = {}
        if request.force:
            backends = await self.metadata_api.get_all_backends(request.from_backend)
            for id, backend in backends.items():
                response[str(id)] = backend.get_proto()
        else:
            # Using a cached version of the backends to avoid querying the KV store for
            # each client request
            for id, backend_client in self.backend_clients.items():
                backend = Backend(
                    id=id,
                    host=backend_client.host,
                    port=backend_client.port,
                    dataclay_id=id,  # wrong: to change or remove completely
                )
                response[str(id)] = backend.get_proto()
        return metadata_pb2.GetAllBackendsResponse(backends=response)

    ###################
    # Object Metadata #
    ###################

    @ServicerMethod(metadata_pb2.GetAllObjectsResponse)
    async def GetAllObjects(self, request, context):
        object_mds = await self.metadata_api.get_all_objects()
        response = {}
        for id, object_md in object_mds.items():
            response[str(id)] = object_md.get_proto()
        return metadata_pb2.GetAllObjectsResponse(objects=response)

    @ServicerMethod(common_pb2.ObjectMetadata)
    async def GetObjectMDById(self, request, context):
        object_md = await self.metadata_api.get_object_md_by_id(UUID(request.object_id))
        return object_md.get_proto()

    @ServicerMethod(common_pb2.ObjectMetadata)
    async def GetObjectMDByAlias(self, request, context):
        object_md = await self.metadata_api.get_object_md_by_alias(
            request.alias_name, request.dataset_name
        )
        return object_md.get_proto()

    #########
    # Alias #
    #########

    @ServicerMethod(Empty)
    async def NewAlias(self, request, context):
        await self.metadata_api.new_alias(
            request.alias_name, request.dataset_name, UUID(request.object_id)
        )
        return Empty()

    @ServicerMethod(metadata_pb2.GetAllAliasResponse)
    async def GetAllAlias(self, request, context):
        aliases = await self.metadata_api.get_all_alias(
            request.dataset_name, str_to_uuid(request.object_id)
        )
        response = {}
        for alias_name, alias in aliases.items():
            response[alias_name] = alias.get_proto()
        return metadata_pb2.GetAllAliasResponse(aliases=response)

    @ServicerMethod(Empty)
    async def DeleteAlias(self, request, context):
        await self.metadata_api.delete_alias(request.alias_name, request.dataset_name)
        return Empty()

    @ServicerMethod(Empty)
    async def Stop(self, request, context):
        logger.warning(
            "Stopping MetadataService. Grace period: %ss", settings.shutdown_grace_period
        )
        get_dc_event_loop().create_task(self.server.stop(settings.shutdown_grace_period))
        return Empty()
