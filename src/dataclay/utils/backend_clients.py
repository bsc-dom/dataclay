import collections
import concurrent.futures
import logging
import threading
import time
from uuid import UUID

from dataclay.backend.client import BackendClient
from dataclay.config import settings
from dataclay.metadata.api import MetadataAPI
from dataclay.metadata.kvdata import Backend

logger = logging.getLogger(__name__)


class BackendClientsManager(collections.abc.MutableMapping):
    """Thread that periodically updates the backend clients."""

    def __init__(self, metadata_api: MetadataAPI):
        self._backend_clients = {}
        self.metadata_api = metadata_api
        self.running = False
        self.lock = threading.Lock()

    def start_update(self):
        """Start the background thread that updates the dictionary."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(
                target=self._update_loop, name="backend-clients-manager", daemon=True
            )
            self.thread.start()

    def stop_update(self):
        """Stop the background thread."""
        self.running = False
        # self.thread.join() # This just makes shutdown slower

    def _update_loop(self):
        while self.running:
            self.update(force=False)
            time.sleep(settings.backend_clients_check_interval)

    def update(self, force: bool = True):
        """Update the backend clients."""
        logger.debug("Updating backend clients...")
        backend_infos = self.metadata_api.get_all_backends(force=force)
        with self.lock:
            for backend_info in backend_infos.values():
                self.add_backend_client(backend_info)

    def add_backend_client(self, backend_info, check_ready=False):
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

        if not check_ready or backend_client.is_ready(settings.timeout_channel_ready):
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
        # Maybe call self.update if the key is not in the dictionary?
        with self.lock:
            return self._backend_clients[key]

    def __setitem__(self, key, value):
        with self.lock:
            self._backend_clients[key] = value

    def __delitem__(self, key):
        with self.lock:
            del self._backend_clients[key]

    def __iter__(self):
        return iter(self._backend_clients.copy())

    def __len__(self):
        return len(self._backend_clients)

    def update_backend_clients_old(self, force: bool = True):
        # The force is only used in the client, to force the access to kvstore
        # otherwise, the metadata service will use the backend clients cache
        # For the backend, the access to kvstore is always forced
        backend_infos = self.metadata_api.get_all_backends(
            from_backend=self.is_backend, force=force
        )
        logger.debug("Updating backend clients. Metadata reports #%d", len(backend_infos))
        new_backend_clients = {}

        # This only applies to the client, or at least, when client settings are set
        use_proxy = settings.client is not None and settings.client.proxy_enabled
        # (Backends will have settings.client = None by default)

        def add_backend_client(backend_info: Backend):
            if (
                backend_info.id in self._backend_clients
                and (
                    use_proxy
                    # The host and port could change, but the id be the same
                    or (
                        backend_info.host == self._backend_clients[backend_info.id].host
                        and backend_info.port == self._backend_clients[backend_info.id].port
                    )
                )
                and self._backend_clients[backend_info.id].is_ready(settings.timeout_channel_ready)
            ):
                logger.debug("Existing backend already available: %s", backend_info.id)
                new_backend_clients[backend_info.id] = self._backend_clients[backend_info.id]
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

            if backend_client.is_ready(settings.timeout_channel_ready):
                new_backend_clients[backend_info.id] = backend_client
            else:
                logger.info("Backend %s gave a timeout, removing it from list", backend_info.id)
                del backend_infos[backend_info.id]

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(add_backend_client, backend_info)
                for backend_info in backend_infos.values()
            ]
            concurrent.futures.wait(futures)
            # results = [future.result() for future in futures]

        logger.debug("Current list of backends: %s", new_backend_clients)
        self._backend_clients = new_backend_clients
