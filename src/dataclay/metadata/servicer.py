from __future__ import annotations

import asyncio
import logging
import traceback
from concurrent import futures
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
from dataclay.runtime import set_dc_event_loop
from dataclay.utils.backend_clients import BackendClientsManager
from dataclay.utils.uuid import str_to_uuid

logger = logging.getLogger(__name__)


async def serve():
    # TODO: Think about moving the dc_event_loop to another place, since
    # metadata don't need to import runtime, but has to define the event loop
    set_dc_event_loop(asyncio.get_running_loop())

    logger.info("Starting MetadataService")
    metadata_api = MetadataAPI(settings.kv_host, settings.kv_port)

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
        settings.dataclay_id = await metadata_api.get_dataclay("this").id
    else:
        await metadata_api.new_superuser(
            settings.root_username, settings.root_password, settings.root_dataset
        )

    server = grpc.aio.server(
        futures.ThreadPoolExecutor(max_workers=settings.thread_pool_max_workers)
    )
    metadata_pb2_grpc.add_MetadataServiceServicer_to_server(
        MetadataServicer(metadata_api, server), server
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
    await server.start()
    logger.info("MetadataService listening on %s", address)

    await server.wait_for_termination()  # Neccessary to keep the server running (cannot use event.wait())


class MetadataServicer(metadata_pb2_grpc.MetadataServiceServicer):
    """Provides methods that implement functionality of metadata server"""

    def __init__(self, metadata_api: MetadataAPI, server: grpc.aio.server):
        self.metadata_api = metadata_api
        self.server = server

        # Start the backend clients manager
        self.backend_clients = BackendClientsManager(metadata_api)
        self.backend_clients.start_update_loop()
        self.backend_clients.start_subscribe()

    # TODO: define get_exception_info(..) to serialize excpetions

    async def NewAccount(self, request, context):
        try:
            await self.metadata_api.new_account(request.username, request.password)
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()
        return Empty()

    async def NewDataset(self, request, context):
        try:
            await self.metadata_api.new_dataset(request.username, request.password, request.dataset)
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()
        return Empty()

    async def GetDataclay(self, request, context):
        try:
            dataclay = await self.metadata_api.get_dataclay(UUID(request.dataclay_id))
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return common_pb2.Dataclay()
        return dataclay.get_proto()

    async def GetAllBackends(self, request, context):
        try:
            response = {}
            if request.force:
                backends = await self.metadata_api.get_all_backends(request.from_backend)
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

    async def GetAllObjects(self, request, context):
        try:
            object_mds = await self.metadata_api.get_all_objects()
            response = {}
            for id, object_md in object_mds.items():
                response[str(id)] = object_md.get_proto()
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return metadata_pb2.GetAllObjectsResponse()
        return metadata_pb2.GetAllObjectsResponse(objects=response)

    async def GetObjectMDById(self, request, context):
        try:
            object_md = await self.metadata_api.get_object_md_by_id(UUID(request.object_id))
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return common_pb2.ObjectMetadata()
        return object_md.get_proto()

    async def GetObjectMDByAlias(self, request, context):
        try:
            object_md = await self.metadata_api.get_object_md_by_alias(
                request.alias_name, request.dataset_name
            )
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return common_pb2.ObjectMetadata()
        return object_md.get_proto()

    #########
    # Alias #
    #########

    async def NewAlias(self, request, context):
        try:
            await self.metadata_api.new_alias(
                request.alias_name, request.dataset_name, UUID(request.object_id)
            )
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()
        return Empty()

    async def GetAllAlias(self, request, context):
        try:
            aliases = await self.metadata_api.get_all_alias(
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

    async def DeleteAlias(self, request, context):
        try:
            await self.metadata_api.delete_alias(request.alias_name, request.dataset_name)
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()
        return Empty()

    async def Stop(self, request, context):
        try:
            logger.info("Stopping MetadataService")
            self.server.stop(5)
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
        return Empty()
