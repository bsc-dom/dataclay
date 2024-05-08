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
    def __init__(self, kv_host: str, kv_port: int, backend_id: UUID):
        # Initialize Metadata Service
        metadata_service = MetadataAPI(kv_host, kv_port)
        super().__init__(metadata_service, backend_id)

        self.backend_id = backend_id

        # NOTE: Previous commits contained deprecated gc code for session and references

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
