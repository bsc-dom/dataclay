""" Class description goes here. """

import asyncio
import logging
import os.path
import signal
from concurrent import futures
from functools import wraps
from typing import Optional
from uuid import UUID, uuid4

import grpc
from google.protobuf.empty_pb2 import Empty
from google.protobuf.wrappers_pb2 import (
    BoolValue,
    BytesValue,
    FloatValue,
    Int32Value,
    StringValue,
)
from grpc_health.v1 import health, health_pb2, health_pb2_grpc

from dataclay.backend.api import BackendAPI
from dataclay.config import session_var, settings
from dataclay.event_loop import get_dc_event_loop, set_dc_event_loop
from dataclay.proto.backend import backend_pb2, backend_pb2_grpc

logger = logging.getLogger(__name__)


def _get_or_generate_backend_id() -> UUID:
    """Try to retrieve this backend UUID, or generate a new one.

    If there is no backend_id defined in the settings, try to get the
    backend UUID. A file may exist in the storage folder (which means that
    this backend already has a identifer, so we should reuse it).

    If there is no UUID in persistent storage, then this means that this is
    the first time this backend has started, so we generate a new one and
    store it.
    """
    backend_id_file = os.path.join(settings.storage_path, "BACKEND_ID")

    if settings.backend.id is None and os.path.exists(backend_id_file):
        # Seems like we will be using a preexisting UUID
        with open(backend_id_file, "rt") as f:
            ret = UUID(f.read())
            logger.info("Starting backend with recovered UUID: %s", ret)
            return ret

    if settings.backend.id is None:
        backend_id = uuid4()
        logger.info("BackendID randomly generated: %s", backend_id)
    else:
        backend_id = settings.backend.id
        logger.info("BackendID defined in settings: %s", backend_id)

    # Store the backend_id and return it
    try:
        with open(backend_id_file, "wt") as f:
            f.write(str(backend_id))
            logger.debug("BackendID has been stored in the following file: %s", backend_id_file)
    except OSError:
        logger.warning(
            "Could not write the BackendID in persistent storage. "
            "Restarting this backend may result in unreachable/unrecoverable objects."
        )
        logger.debug("Exception when trying to access persistent backend id file:", exc_info=True)
    return backend_id


async def serve():

    # Set the event loop created by `asyncio.run` as the dataclay event loop
    set_dc_event_loop(asyncio.get_running_loop())

    backend_id = _get_or_generate_backend_id()

    logger.info("Starting backend service...")
    backend = BackendAPI(
        settings.backend.name,
        settings.backend.port,
        backend_id,
        settings.kv_host,
        settings.kv_port,
    )

    # Wait for the KV store to be ready
    if not await backend.is_ready(timeout=10):
        raise RuntimeError("KV store is not ready. Aborting!")

    # Initialize the servicer
    server = grpc.aio.server(
        options=[
            ("grpc.max_send_message_length", -1),
            ("grpc.max_receive_message_length", -1),
        ],
    )
    backend_servicer = BackendServicer(backend, server)
    backend_pb2_grpc.add_BackendServiceServicer_to_server(backend_servicer, server)

    # Enable healthcheck for the server
    if settings.backend.enable_healthcheck:
        logger.info("Enabling healthcheck for BackendService")
        health_servicer = health.HealthServicer(
            experimental_non_blocking=True,
            experimental_thread_pool=futures.ThreadPoolExecutor(
                max_workers=settings.healthcheck_max_workers
            ),
        )
        health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)
        health_servicer.set(
            "dataclay.proto.backend.BackendService", health_pb2.HealthCheckResponse.SERVING
        )

    # Start the server
    address = f"{settings.backend.listen_address}:{settings.backend.port}"
    server.add_insecure_port(address)
    await server.start()
    logger.info("Backend service listening on %s", address)

    # Autoregister of backend to KV store
    await backend.runtime.metadata_service.register_backend(
        backend_id,
        settings.backend.host,
        settings.backend.port,
        settings.dataclay_id,
    )

    # Register signal handlers for graceful termination
    loop = get_dc_event_loop()
    for sig in [signal.SIGINT, signal.SIGTERM]:
        loop.add_signal_handler(
            sig, lambda: loop.create_task(server.stop(settings.shutdown_grace_period))
        )

    # Wait for the server to stop
    logger.info("Backend service started")
    await server.wait_for_termination()
    logger.info("Backend service stopped")
    await backend.stop()


class ServicerMethod:
    def __init__(self, ret_factory):
        self.ret_factory = ret_factory

    @staticmethod
    def _validate_context(servicer, context) -> Optional[str]:
        metadata = dict(context.invocation_metadata())

        # Check if the backend-id metadata field matches this backend
        # There are scenarios in which backend-id will not be set, and that
        # is not an issue. However, a mismatch is a strange scenario, which
        # warrants at least an error log.
        if "backend-id" in metadata:
            if metadata["backend-id"] != str(servicer.backend.backend_id):
                logger.error(
                    "The gRPC call was intended for backend_id=%s. We are %s. Failure.",
                    metadata["backend-id"],
                    servicer.backend.backend_id,
                )
                return "Invalid backend-id"
        else:
            logger.debug("No backend-id metadata header in the call.")

        # set the current_context
        if "dataset-name" in metadata and "username" in metadata:
            session_var.set(
                {
                    "dataset_name": metadata["dataset-name"],
                    "username": metadata["username"],
                    "token": b"",
                }
            )
        return None

    def __call__(self, func):
        @wraps(func)
        async def wrapper(servicer, request, context):
            if error_details := self._validate_context(servicer, context):
                context.set_details(error_details)
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                return self.ret_factory()
            try:
                return await func(servicer, request, context)
            except Exception as e:
                context.set_details(str(e))
                context.set_code(grpc.StatusCode.INTERNAL)
                logger.info("Exception during gRPC call\n", exc_info=True)
                return self.ret_factory()

        return wrapper


class BackendServicer(backend_pb2_grpc.BackendServiceServicer):
    def __init__(self, backend: BackendAPI, server: grpc.aio.Server):
        """Execution environment being managed"""
        self.backend = backend
        self.server = server

    @ServicerMethod(Empty)
    async def RegisterObjects(self, request, context):
        await self.backend.register_objects(request.dict_bytes, request.make_replica)
        return Empty()

    @ServicerMethod(Empty)
    async def MakePersistent(self, request, context):
        await self.backend.make_persistent(request.pickled_obj)
        return Empty()

    @ServicerMethod(backend_pb2.CallActiveMethodResponse)
    async def CallActiveMethod(self, request, context):
        exec_constraints = {}
        for key, any_value in request.exec_constraints.items():
            if any_value.Is(Int32Value.DESCRIPTOR):
                value = Int32Value()
                any_value.Unpack(value)
                exec_constraints[key] = value.value
            elif any_value.Is(FloatValue.DESCRIPTOR):
                value = FloatValue()
                any_value.Unpack(value)
                exec_constraints[key] = value.value
            elif any_value.Is(StringValue.DESCRIPTOR):
                value = StringValue()
                any_value.Unpack(value)
                exec_constraints[key] = value.value
            elif any_value.Is(BoolValue.DESCRIPTOR):
                value = BoolValue()
                any_value.Unpack(value)
                exec_constraints[key] = value.value
            else:
                raise ValueError(f"Unknown type for {key}: {any_value}")

        value, is_exception = await self.backend.call_active_method(
            UUID(request.object_id),
            request.method_name,
            request.args,
            request.kwargs,
            exec_constraints,
        )
        return backend_pb2.CallActiveMethodResponse(value=value, is_exception=is_exception)

    #################
    # Store Methods #
    #################

    @ServicerMethod(backend_pb2.GetObjectAttributeResponse)
    async def GetObjectAttribute(self, request, context):
        value, is_exception = await self.backend.get_object_attribute(
            UUID(request.object_id),
            request.attribute,
        )
        return backend_pb2.GetObjectAttributeResponse(value=value, is_exception=is_exception)

    @ServicerMethod(backend_pb2.SetObjectAttributeResponse)
    async def SetObjectAttribute(self, request, context):
        value, is_exception = await self.backend.set_object_attribute(
            UUID(request.object_id),
            request.attribute,
            request.serialized_attribute,
        )
        return backend_pb2.SetObjectAttributeResponse(value=value, is_exception=is_exception)

    @ServicerMethod(backend_pb2.DelObjectAttributeResponse)
    async def DelObjectAttribute(self, request, context):
        value, is_exception = await self.backend.del_object_attribute(
            UUID(request.object_id),
            request.attribute,
        )
        return backend_pb2.DelObjectAttributeResponse(value=value, is_exception=is_exception)

    @ServicerMethod(BytesValue)
    async def GetObjectProperties(self, request, context):
        result = await self.backend.get_object_properties(UUID(request.object_id))
        return BytesValue(value=result)

    @ServicerMethod(Empty)
    async def UpdateObjectProperties(self, request, context):
        await self.backend.update_object_properties(
            UUID(request.object_id), request.serialized_properties
        )
        return Empty()

    @ServicerMethod(backend_pb2.NewObjectVersionResponse)
    async def NewObjectVersion(self, request, context):
        result = await self.backend.new_object_version(UUID(request.object_id))
        return backend_pb2.NewObjectVersionResponse(object_info=result)

    @ServicerMethod(Empty)
    async def ConsolidateObjectVersion(self, request, context):
        await self.backend.consolidate_object_version(UUID(request.object_id))
        return Empty()

    @ServicerMethod(Empty)
    async def ProxifyObject(self, request, context):
        await self.backend.proxify_object(UUID(request.object_id), UUID(request.new_object_id))
        return Empty()

    @ServicerMethod(Empty)
    async def ChangeObjectId(self, request, context):
        await self.backend.change_object_id(UUID(request.object_id), UUID(request.new_object_id))
        return Empty()

    @ServicerMethod(Empty)
    async def SendObjects(self, request, context):
        await self.backend.send_objects(
            map(UUID, request.object_ids),
            UUID(request.backend_id),
            request.make_replica,
            request.recursive,
            request.remotes,
        )
        return Empty()

    @ServicerMethod(Empty)
    async def FlushAll(self, request, context):
        logger.info("Flushing all objects")
        await self.backend.flush_all()
        return Empty()

    @ServicerMethod(Empty)
    async def Stop(self, request, context):
        logger.info("Stopping backend. Grace period: %ss", settings.shutdown_grace_period)
        get_dc_event_loop().create_task(self.server.stop(settings.shutdown_grace_period))
        return Empty()

    @ServicerMethod(Empty)
    async def Drain(self, request, context):
        logger.info("Draining backend. Grace period: %ss", settings.shutdown_grace_period)
        await self.backend.move_all_objects()
        get_dc_event_loop().create_task(self.server.stop(settings.shutdown_grace_period))
        return Empty()

    @ServicerMethod(Empty)
    async def NewObjectReplica(self, request, context):
        await self.backend.new_object_replica(
            UUID(request.object_id),
            UUID(request.backend_id),
            request.recursive,
            request.remotes,
        )
        return Empty()
