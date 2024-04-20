import collections
import concurrent.futures
import logging
import threading
import time
from uuid import UUID
import asyncio

from dataclay.backend.client import BackendClient
from dataclay.config import settings
from dataclay.metadata.api import MetadataAPI
from dataclay.metadata.kvdata import Backend
from dataclay.runtime import get_dc_event_loop

logger = logging.getLogger(__name__)


class BackendClientsManager(collections.abc.MutableMapping):
    """Thread that periodically updates the backend clients."""

    def __init__(self, metadata_api: MetadataAPI):
        self._backend_clients = {}
        self.metadata_api = metadata_api
        self.update_task = None

    async def get(self, key) -> BackendClient:
        try:
            return self._backend_clients[key]
        except KeyError:
            await self.update()
            return self._backend_clients[key]

    def start_update(self):
        """Start the background thread that updates the dictionary."""
        if self.update_task is None or self.update_task.done():
            loop = get_dc_event_loop()
            self.update_task = loop.create_task(self._update_loop())
        else:
            logger.warning("Update loop is already running")

    async def _update_loop(self):
        try:
            while True:
                logger.debug("Update loop running")
                await self.update(force=False)
                await asyncio.sleep(settings.backend_clients_check_interval)
        except asyncio.CancelledError:
            logger.info("Update loop has been cancelled.")
            raise

    def stop_update(self):
        """Stop the background thread."""
        if self.update_task:
            self.update_task.cancel()

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
        """Subscribe to the new-backend-client and del-backend-client pub/sub topics. Only for backends"""
        self.pubsub = self.metadata_api.kv_manager.r_client.pubsub()
        self.pubsub.subscribe(
            **{
                "new-backend-client": self._new_backend_handler,
                "del-backend-client": self._del_backend_handler,
            }
        )
        self.pubsub_thread = self.pubsub.run_in_thread(sleep_time=0.001, daemon=True)

    def _new_backend_handler(self, message):
        backend_info = Backend.from_json(message["data"])
        logger.debug("Received new-backend-client publication: %s", backend_info.id)
        self.add_backend_client(backend_info)

    def _del_backend_handler(self, message):
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
