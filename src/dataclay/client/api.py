"""Common library client API for dataClay.

Runtime.
Note that importing this module has a basic semantic: it prepares the dataClay
core and sets the "client" mode for the library.
"""

from __future__ import annotations

__all__ = ["init", "finish", "DataClayObject"]

import asyncio
import logging
import logging.config
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from dataclay.config import (
    ClientSettings,
    get_runtime,
    session_var,
    set_runtime,
    settings,
)
from dataclay.event_loop import EventLoopThread, get_dc_event_loop, set_dc_event_loop
from dataclay.runtime import ClientRuntime
from dataclay.utils.telemetry import trace

if TYPE_CHECKING:
    from uuid import UUID

    from dataclay.backend.client import BackendClient
    from dataclay.dataclay_object import DataClayObject

# This will be populated during initialization
# LOCAL = _UNDEFINED_LOCAL

tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)

_telemetry_started = False


def start_telemetry():
    global _telemetry_started
    if _telemetry_started:
        return

    if settings.service_name is None:
        settings.service_name = "client"

    if settings.tracing:
        # pylint: disable=import-outside-toplevel
        import dataclay.utils.telemetry

        dataclay.utils.telemetry.set_tracing(
            settings.service_name,
            settings.tracing_host,
            settings.tracing_port,
            settings.tracing_exporter,
        )

    if settings.metrics:
        # pylint: disable=import-outside-toplevel
        import dataclay.utils.metrics

        dataclay.utils.metrics.set_metrics(
            settings.metrics_host,
            settings.metrics_port,
            settings.metrics_exporter,
        )

    _telemetry_started = True


def init():
    client_api = Client()
    client_api.start()
    return client_api


def finish():
    pass


class Client:
    """Client API for dataClay.

    Usually you create client instance and call start() method to initialize it.

        from dataclay import client
        client = dataclay.client(host="127.0.0.1")
        client.start()
    """

    settings: ClientSettings
    runtime: ClientRuntime
    previous_settings: Optional[ClientSettings]
    previous_runtime: Optional[ClientRuntime]

    is_active: bool = False

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        dataset: Optional[str] = None,
        local_backend: Optional[str] = None,
        proxy_host: Optional[str] = None,
        proxy_port: Optional[int] = None,
    ):
        # Set settings
        settings_kwargs = {}
        if host:
            settings_kwargs["dataclay_host"] = host
        if port:
            settings_kwargs["dataclay_port"] = port
        if username:
            settings_kwargs["username"] = username
        if password:
            settings_kwargs["password"] = password
        if dataset:
            settings_kwargs["dataset"] = dataset
        if local_backend:
            settings_kwargs["local_backend"] = local_backend
        if proxy_host:
            settings_kwargs["proxy_host"] = proxy_host
            settings_kwargs["proxy_enabled"] = True
        if proxy_port:
            settings_kwargs["proxy_port"] = proxy_port
            settings_kwargs["proxy_enabled"] = True

        self.settings = ClientSettings(**settings_kwargs)

        start_telemetry()

        # Set local backend
        # if settings.LOCAL_BACKEND:
        #     for ee_id, ee_info in self.runtime.ee_infos.items():
        #         if ee_info.sl_name == settings.LOCAL_BACKEND:
        #             global LOCAL
        #             LOCAL = ee_id
        #             break
        #     else:
        #         logger.warning("Backend with name '%s' not found, ignoring", settings.LOCAL_BACKEND)

    @tracer.start_as_current_span("start")
    def start(self):
        """Start the client runtime"""

        if self.is_active:
            logger.warning("Client already active. Ignoring")
            return

        logger.info("Starting client runtime")

        # Create new event loop in a new thread
        loop = asyncio.new_event_loop()
        set_dc_event_loop(loop)
        event_loop_thread = EventLoopThread(loop)
        event_loop_thread.start()
        event_loop_thread.ready.wait()

        # Replace settings
        self.previous_settings = settings.client
        settings.client = self.settings

        # Create and replace runtime
        self.previous_runtime = get_runtime()

        if settings.client.proxy_enabled:
            logger.debug(
                "Using proxy connection to %s:%s",
                settings.client.proxy_host,
                settings.client.proxy_port,
            )
            self.runtime = ClientRuntime(settings.client.proxy_host, settings.client.proxy_port)
        else:
            self.runtime = ClientRuntime(
                settings.client.dataclay_host, settings.client.dataclay_port
            )

        future = asyncio.run_coroutine_threadsafe(self.runtime.start(), loop)
        future.result()

        set_runtime(self.runtime)

        session_var.set(
            {"dataset_name": settings.client.dataset, "username": settings.client.username}
        )

        # Cache the dataclay_id, to avoid later request
        # self.runtime.dataclay_id

        self.is_active = True

    @tracer.start_as_current_span("stop")
    def stop(self):
        """Stop the client runtime"""
        if not self.is_active:
            logger.warning("Client is not active. Ignoring")
            return

        logger.info("Stopping client runtime")
        asyncio.run_coroutine_threadsafe(self.runtime.stop(), get_dc_event_loop()).result()
        settings.client = self.previous_settings
        set_runtime(self.previous_runtime)
        self.is_active = False
        logger.info("Client runtime stopped")

    def __del__(self):
        # BUG: When calling stop() from __del__, it hangs the program at `run_coroutine_threadsafe`
        # self.stop()
        if self.is_active:
            logger.warning("Client instance deleted without calling stop() for a clean shutdown")
        pass

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()

    async def __aenter__(self):
        self.start()
        return self

    async def __aexit__(self, *excinfo):
        self.stop()

    @tracer.start_as_current_span("get_backends")
    def get_backends(self) -> dict[UUID, BackendClient]:
        if not self.is_active:
            raise RuntimeError("Client is not active")
        asyncio.run_coroutine_threadsafe(
            self.runtime.backend_clients.update(), get_dc_event_loop()
        ).result()
        return self.runtime.backend_clients

    @tracer.start_as_current_span("a_get_backends")
    async def a_get_backends(self) -> dict[UUID, BackendClient]:
        if not self.is_active:
            raise RuntimeError("Client is not active")
        future = asyncio.run_coroutine_threadsafe(
            self.runtime.backend_clients.update(), get_dc_event_loop()
        )
        await asyncio.wrap_future(future)
        return self.runtime.backend_clients


###############
# To Refactor #
###############


# def register_dataclay(id, host, port):
#     """Register external dataClay for federation
#     Args:
#         host: external dataClay host name
#         port: external dataClay port
#     """
#     return get_runtime().register_external_dataclay(id, host, port)


# def unfederate(ext_dataclay_id=None):
#     """Unfederate all objects belonging to/federated with external data clay with id provided
#     or with all any external dataclay if no argument provided.
#     :param ext_dataclay_id: external dataClay id
#     :return: None
#     :type ext_dataclay_id: uuid
#     :rtype: None
#     """
#     if ext_dataclay_id is not None:
#         return get_runtime().unfederate_all_objects(ext_dataclay_id)
#     else:
#         return get_runtime().unfederate_all_objects_with_all_dcs()


# def migrate_federated_objects(origin_dataclay_id, dest_dataclay_id):
#     """Migrate federated objects from origin dataclay to destination dataclay
#     :param origin_dataclay_id: origin dataclay id
#     :param dest_dataclay_id destination dataclay id
#     :return: None
#     :rtype: None
#     """
#     return get_runtime().migrate_federated_objects(origin_dataclay_id, dest_dataclay_id)


# def federate_all_objects(dest_dataclay_id):
#     """Federate all objects from current dataclay to destination dataclay
#     :param dest_dataclay_id destination dataclay id
#     :return: None
#     :rtype: None
#     """
#     return get_runtime().federate_all_objects(dest_dataclay_id)
