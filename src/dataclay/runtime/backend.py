""" BackendRuntime """

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from dataclay.config import settings
from dataclay.exceptions import *
from dataclay.metadata.api import MetadataAPI
from dataclay.runtime.runtime import DataClayRuntime

if TYPE_CHECKING:
    from uuid import UUID

logger = logging.getLogger(__name__)


class BackendRuntime(DataClayRuntime):
    # data_manager: DataManager = None

    def __init__(self, kv_host: str, kv_port: int, backend_id: UUID):
        # Initialize Metadata Service
        metadata_service = MetadataAPI(kv_host, kv_port)
        super().__init__(metadata_service, backend_id)

        # Initialize DataManager
        # self.data_manager = DataManager()
        # self.data_manager.start_memory_monitor()

        self.backend_id = backend_id

        # DEPRECATED
        # References hold by sessions. Resource note: Maximum size of this map is maximum number of objects allowed in EE x sessions.
        # Also, important to think what happens if one single session is associated to two client threads? use case?
        # should we allow that?
        # Must be thread-safe.
        # self.references_hold_by_sessions = {}

        # Sessions in quarantine. note: maximum size of this map is max number of sessions per EE: This map is needed to solve a race
        # condition in Global Garbage collection (@see getReferenceCounting).
        # self.quarantine_sessions = set()

        # Per each session, it's expiration date. This is used to control 'retained' objects from sessions in Garbage collection.
        # Must be thread-safe.
        # self.session_expires_dates = {}

    async def stop(self):
        # Stop all backend clients
        await self.backend_clients.stop()

        # Remove backend entry from metadata
        await self.metadata_service.delete_backend(self.backend_id)

        # Stop DataManager memory monitor
        self.data_manager.stop_memory_monitor()

        # Flush all data if not ephemeral
        if not settings.ephemeral:
            await self.data_manager.flush_all()

        # Stop metadata redis connection
        await self.metadata_service.close()

    # DEPRECATED

    # def synchronize(self, instance, operation_name, params):
    #     raise Exception("To refactor")
    #     session_id = self.session.id
    #     object_id = instance._dc_meta.id
    #     operation = self.get_operation_info(instance._dc_meta.id, operation_name)
    #     implementation_id = self.get_implementation_id(instance._dc_meta.id, operation_name)
    #     # === SERIALIZE PARAMETERS ===
    #     serialized_params = SerializationLibUtilsSingleton.serialize_params_or_return(
    #         params=[params],
    #         iface_bitmaps=None,
    #         params_spec=operation.params,
    #         params_order=operation.paramsOrder,
    #         hint_volatiles=instance._dc_meta.master_backend_id,
    #         runtime=self,
    #     )
    #     self.execution_environment.synchronize(
    #         session_id, object_id, implementation_id, serialized_params
    #     )

    # # Federations

    # def federate_to_backend(self, dc_obj, external_execution_environment_id, recursive):
    #     raise Exception("To refactor")
    #     object_id = dc_obj._dc_meta.id
    #     session_id = self.session.id
    #     logger.debug(
    #         "[==FederateObject==] Starting federation of object by %s with dest dataClay %s, and session %s",
    #         object_id,
    #         external_execution_environment_id,
    #         session_id,
    #     )
    #     self.execution_environment.federate(
    #         session_id, object_id, external_execution_environment_id, recursive
    #     )

    # def unfederate_from_backend(self, dc_obj, external_execution_environment_id, recursive):
    #     raise Exception("To refactor")
    #     object_id = dc_obj._dc_meta.id
    #     session_id = self.session.id
    #     logger.debug(
    #         "[==UnfederateObject==] Starting unfederation of object %s with ext backend %s, and session %s",
    #         object_id,
    #         external_execution_environment_id,
    #         session_id,
    #     )
    #     self.execution_environment.unfederate(
    #         session_id, object_id, external_execution_environment_id, recursive
    #     )
