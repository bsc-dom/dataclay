"""Common library client API for dataClay.

Runtime.
Note that importing this module has a basic semantic: it prepares the dataClay
core and sets the "client" mode for the library.
"""

__all__ = ["init", "finish", "DataClayObject"]

import logging
import logging.config
from typing import TYPE_CHECKING
from uuid import UUID

import dataclay.utils.metrics
import dataclay.utils.telemetry
from dataclay.backend.client import BackendClient
from dataclay.config import ClientSettings, settings
from dataclay.dataclay_object import DataClayObject
from dataclay.runtime import get_runtime, set_runtime
from dataclay.runtime.client import ClientRuntime
from dataclay.utils.telemetry import trace

if TYPE_CHECKING:
    from uuid import UUID

    from dataclay.backend.client import BackendClient

# This will be populated during initialization
# LOCAL = _UNDEFINED_LOCAL

tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)


def init():
    client_api = Client()
    client_api.start()
    return client_api


def finish():
    pass


_telemetry_started = False


def start_telemetry():
    global _telemetry_started
    if _telemetry_started:
        return

    if settings.service_name is None:
        settings.service_name = "client"

    if settings.tracing:
        dataclay.utils.telemetry.set_tracing(
            settings.service_name,
            settings.tracing_host,
            settings.tracing_port,
            settings.tracing_exporter,
        )

    if settings.metrics:
        dataclay.utils.metrics.set_metrics(
            settings.metrics_host,
            settings.metrics_port,
            settings.metrics_exporter,
        )

    _telemetry_started = True


class Client:
    """Client API for dataClay.

    Usually you create client instance and call start() method to initialize it.

        from dataclay import client
        client = dataclay.client(host="127.0.0.1", username="testuser", password="s3cret", dataset="testuser")



    """

    def __init__(
        self, host=None, port=None, username=None, password=None, dataset=None, local_backend=None
    ):
        client_settings_kwargs = {}
        if host:
            client_settings_kwargs["dataclay_host"] = host
        if port:
            client_settings_kwargs["dataclay_port"] = port
        if username:
            client_settings_kwargs["username"] = username
        if password:
            client_settings_kwargs["password"] = password
        if dataset:
            client_settings_kwargs["dataset"] = dataset
        if local_backend:
            client_settings_kwargs["local_backend"] = local_backend

        self.client_settings = ClientSettings(**client_settings_kwargs)

        self.is_initialized = False

        start_telemetry()

        # Set LOCAL_BACKEND
        # if settings.LOCAL_BACKEND:
        #     for ee_id, ee_info in self.runtime.ee_infos.items():
        #         if ee_info.sl_name == settings.LOCAL_BACKEND:
        #             global LOCAL
        #             LOCAL = ee_id
        #             break
        #     else:
        #         logger.warning(f"Backend with name '{settings.LOCAL_BACKEND}' not found, ignoring")

    @tracer.start_as_current_span("start")
    def start(self):
        """Initialize the client API.

        Note that after a successful call to this method, subsequent calls will be
        a no-operation.
        """

        if self.is_initialized:
            logger.warning("Already initialized. Ignoring")
            return

        logger.info("Initializing client")

        # Update settings
        self.old_client_settings = settings.client
        settings.client = self.client_settings

        # Create a new runtime
        self.old_runtime = get_runtime()
        self.runtime = ClientRuntime(settings.client.dataclay_host, settings.client.dataclay_port)
        set_runtime(self.runtime)

        # Create a new session
        self.session = self.runtime.metadata_service.new_session(
            settings.client.username,
            settings.client.password.get_secret_value(),
            settings.client.dataset,
        )
        self.runtime.session = self.session
        self.runtime.metadata_service.session = self.session

        # Cache the backends clients
        self.runtime.update_backend_clients()

        # Cache the dataclay_id, to avoid later request
        # self.runtime.dataclay_id

        logger.debug(f"Started session {self.session.id}")
        self.is_initialized = True

    @tracer.start_as_current_span("stop")
    def stop(self):
        """Finish the client API."""

        if not self.is_initialized:
            logger.warning("Already finished. Ignoring")
            return

        logger.info("Finishing client API")
        self.runtime.stop()
        settings.client = self.old_client_settings
        set_runtime(self.old_runtime)
        self.is_initialized = False

    def __del__(self):
        self.stop()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()

    @tracer.start_as_current_span("get_backends")
    def get_backends(self) -> dict[UUID:BackendClient]:
        """Return a dictionary of backends clients."""
        self.runtime.update_backend_clients()
        return self.runtime.backend_clients


##########
# Dataclay
##########


def register_dataclay(id, host, port):
    """Register external dataClay for federation
    Args:
        host: external dataClay host name
        port: external dataClay port
    """
    return get_runtime().register_external_dataclay(id, host, port)


def unfederate(ext_dataclay_id=None):
    """Unfederate all objects belonging to/federated with external data clay with id provided
    or with all any external dataclay if no argument provided.
    :param ext_dataclay_id: external dataClay id
    :return: None
    :type ext_dataclay_id: uuid
    :rtype: None
    """
    if ext_dataclay_id is not None:
        return get_runtime().unfederate_all_objects(ext_dataclay_id)
    else:
        return get_runtime().unfederate_all_objects_with_all_dcs()


def migrate_federated_objects(origin_dataclay_id, dest_dataclay_id):
    """Migrate federated objects from origin dataclay to destination dataclay
    :param origin_dataclay_id: origin dataclay id
    :param dest_dataclay_id destination dataclay id
    :return: None
    :rtype: None
    """
    return get_runtime().migrate_federated_objects(origin_dataclay_id, dest_dataclay_id)


def federate_all_objects(dest_dataclay_id):
    """Federate all objects from current dataclay to destination dataclay
    :param dest_dataclay_id destination dataclay id
    :return: None
    :rtype: None
    """
    return get_runtime().federate_all_objects(dest_dataclay_id)


######################################
# Static initialization of dataClay
##########################################################

# The client should never need the delete methods of persistent objects
# ... not doing this is a performance hit
# del DataClayObject.__del__


# initialize()


# Now the logger is ready
# logger.debug("Client-mode initialized, dataclay.commonruntime should be ready")
