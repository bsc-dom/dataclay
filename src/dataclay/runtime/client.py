""" ClientRuntime """

from __future__ import annotations

import logging
import traceback

from dataclay.exceptions import *
from dataclay.metadata.client import MetadataClient
from dataclay.runtime.runtime import DataClayRuntime
from dataclay.utils.telemetry import trace

tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)


class ClientRuntime(DataClayRuntime):
    def __init__(self, metadata_service_host: str, metadata_service_port: int):
        metadata_service = MetadataClient(metadata_service_host, metadata_service_port)
        super().__init__(metadata_service)

    @property
    def data_manager(self):
        raise DataClayException("Client has no data manager")

    ############
    # Replicas #
    ############

    def synchronize(self, instance, operation_name, params):
        raise Exception("To refactor")
        dest_backend_id = self.get_hint()
        operation = self.get_operation_info(instance._dc_meta.id, operation_name)
        implementation_id = self.get_implementation_id(instance._dc_meta.id, operation_name)
        # === SERIALIZE PARAMETER ===
        serialized_params = SerializationLibUtilsSingleton.serialize_params_or_return(
            params=[params],
            iface_bitmaps=None,
            params_spec=operation.params,
            params_order=operation.paramsOrder,
            hint_volatiles=instance._dc_meta.master_backend_id,
            runtime=self,
        )

        ee_client = self.get_backend_client(dest_backend_id)
        ee_client.synchronize(
            self.session.id, instance._dc_meta.id, implementation_id, serialized_params
        )

    ##############
    # Federation #
    ##############

    def federate_to_backend(self, instance, external_execution_environment_id, recursive):
        raise Exception("To refactor")

        hint = instance._dc_meta.master_backend_id
        if hint is None:
            self.sync_object_metadata(instance)
            hint = self.get_hint()

        ee_client = self.get_backend_client(hint)

        logger.debug(
            "[==FederateObject==] Starting federation of object by %s calling EE %s with dest dataClay %s, and session %s",
            instance._dc_meta.id,
            hint,
            external_execution_environment_id,
            self.session.id,
        )
        ee_client.federate(
            self.session.id, instance._dc_meta.id, external_execution_environment_id, recursive
        )

    def unfederate_from_backend(self, instance, external_execution_environment_id, recursive):

        raise Exception("To refactor")

        logger.debug(
            "[==UnfederateObject==] Starting unfederation of object %s with ext backend %s, and session %s",
            instance._dc_meta.id,
            external_execution_environment_id,
            self.session.id,
        )
        hint = instance._dc_meta.master_backend_id
        if hint is None:
            self.sync_object_metadata(instance)
            hint = self.get_hint()
        ee_client = self.get_backend_client(hint)

        ee_client.unfederate(
            self.session.id, instance._dc_meta.id, external_execution_environment_id, recursive
        )

    ############
    # Shutdown #
    ############

    async def stop(self):
        await self.backend_clients.stop()
        await self.metadata_service.close()
