""" ClientRuntime """

from __future__ import annotations

import logging

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

    # NOTE: Previous commits contained deprecated syncronize, federate and unfederate methods

    ############
    # Shutdown #
    ############

    async def stop(self):
        await self.backend_clients.stop()
        await self.metadata_service.close()
