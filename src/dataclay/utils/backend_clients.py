from __future__ import annotations

import asyncio
import collections
import logging
from typing import TYPE_CHECKING
from uuid import UUID

from dataclay.backend.client import BackendClient
from dataclay.config import settings
from dataclay.event_loop import get_dc_event_loop
from dataclay.metadata.api import MetadataAPI
from dataclay.metadata.kvdata import Backend
from dataclay.utils.telemetry import trace

if TYPE_CHECKING:
    from dataclay.metadata.client import MetadataClient

tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)


class BackendClientsManager(collections.abc.MutableMapping):
    """Thread that periodically updates the backend clients."""

    def __init__(self, metadata_api: MetadataAPI | MetadataClient):
        self._backend_clients: dict[UUID, BackendClient] = {}
        self.metadata_api = metadata_api
        self.update_task = None
        self.pubsub = None
        self.worker_task = None

    async def get(self, key) -> BackendClient:
        try:
            return self._backend_clients[key]
        except KeyError:
            await self.update()
            return self._backend_clients[key]

    def start_update_loop(self):
        """Start the background thread that updates the dictionary."""
        if self.update_task is None or self.update_task.done():
            self.update_task = get_dc_event_loop().create_task(self._update_loop())
        else:
            logger.warning("Update loop is already running")

    def stop_update_loop(self):
        """Stop the background thread."""
        if self.update_task:
            self.update_task.cancel()

    async def _update_loop(self):
        try:
            while True:
                await self.update(force=False)
                await asyncio.sleep(settings.backend_clients_check_interval)
        except asyncio.CancelledError:
            logger.info("Update loop has been cancelled.")
            raise

    @tracer.start_as_current_span("update")
    async def update(self, force: bool = True):
        """Update the backend clients.

        If force is True, the backend clients will be updated directly from the kv.
        If force is False, the backend clients will be updated with the metadata backends cache.
        """
        logger.debug("Updating backend clients")
        backend_infos = await self.metadata_api.get_all_backends(force=force)

        for backend_info in backend_infos.values():
            await self.add_backend_client(backend_info)

    async def add_backend_client(self, backend_info, check_ready=False):
        # This only applies to the client, or at least, when client settings are set
        use_proxy = settings.client is not None and settings.client.proxy_enabled
        # (Backends will have settings.client = None by default)

        if backend_info.id in self._backend_clients and (
            use_proxy
            or (
                backend_info.host == self._backend_clients[backend_info.id].host
                and backend_info.port == self._backend_clients[backend_info.id].port
            )
        ):
            logger.debug("Existing backend already available: %s", backend_info.id)
            if check_ready and not self._backend_clients[backend_info.id].is_ready(
                settings.timeout_channel_ready
            ):
                logger.info("Backend %s gave a timeout, removing it from list", backend_info.id)
                del self._backend_clients[backend_info.id]
            else:
                if check_ready:
                    logger.debug("Existing backend is ready: %s", backend_info.id)
                return

        if use_proxy:
            logger.debug("New backend %s, connecting through proxy", backend_info.id)
            backend_client = BackendClient(
                settings.client.proxy_host,
                settings.client.proxy_port,
                backend_id=backend_info.id,
            )

        else:
            logger.debug(
                "New backend %s at %s:%s", backend_info.id, backend_info.host, backend_info.port
            )
            backend_client = BackendClient(
                backend_info.host, backend_info.port, backend_id=backend_info.id
            )

        if not check_ready or await backend_client.is_ready(settings.timeout_channel_ready):
            self._backend_clients[backend_info.id] = backend_client

        else:
            logger.info("Backend %s gave a timeout, removing it from list", backend_info.id)
            del self._backend_clients[backend_info.id]

    def start_subscribe(self):
        """Subscribe to the new-backend-client and del-backend-client pub/sub topics"""
        if not isinstance(self.metadata_api, MetadataAPI):
            logger.warning("Pub/sub not available. Access to kv data is not allowed for clients.")
            return

        self.pubsub = self.metadata_api.kv_manager.pubsub()
        self.worker_task = get_dc_event_loop().create_task(self._pubsub_worker())

    async def stop_subscribe(self):
        """Unsubscribe from the pub/sub topics."""
        if self.worker_task:
            self.worker_task.cancel()
            await self.pubsub.close()

    async def _pubsub_worker(self):
        await self.pubsub.subscribe(
            "new-backend-client",
            "del-backend-client",
        )
        async for message in self.pubsub.listen():
            if message["type"] == "message":
                if message["channel"].decode() == "new-backend-client":
                    backend_info = Backend.from_json(message["data"])
                    logger.debug("Received new-backend-client publication: %s", backend_info.id)
                    await self.add_backend_client(backend_info)
                elif message["channel"].decode() == "del-backend-client":
                    backend_id = UUID(message["data"].decode())
                    logger.debug("Received del-backend-client publication: %s", backend_id)
                    if backend_id in self._backend_clients:
                        del self._backend_clients[backend_id]

    def __getitem__(self, key) -> BackendClient:
        return self._backend_clients[key]

    def __setitem__(self, key, value):
        self._backend_clients[key] = value

    def __delitem__(self, key):
        del self._backend_clients[key]

    def __iter__(self):
        return iter(self._backend_clients.copy())

    def __len__(self):
        return len(self._backend_clients)

    async def stop(self):
        """Stop the background task and close the pubsub connection."""
        self.stop_update_loop()
        await self.stop_subscribe()
        for backend_id, backend_client in self._backend_clients.items():
            logger.debug("Closing client connection to %s", backend_id)
            backend_client.close()
