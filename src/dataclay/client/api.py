"""Common library client API for dataClay.

Runtime.
Note that importing this module has a basic semantic: it prepares the dataClay
core and sets the "client" mode for the library.
"""

__all__ = ["init", "finish", "DataClayObject"]

import logging
import logging.config

from dataclay.client.runtime import UNDEFINED_LOCAL as _UNDEFINED_LOCAL
from dataclay.client.runtime import ClientRuntime
from dataclay.conf import settings
from dataclay.dataclay_object import DataClayObject
from dataclay.runtime import get_runtime, set_runtime
from dataclay.utils.tracing import trace

# This will be populated during initialization
LOCAL = _UNDEFINED_LOCAL

tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)


def client(host=None, port=None, username=None, password=None, dataset=None, local_backend=None):
    return ClientAPI(
        host=host,
        port=port,
        username=username,
        password=password,
        dataset=dataset,
        local_backend=local_backend,
    )


def init():
    client_api = ClientAPI()
    client_api.start()
    return client_api


def finish():
    pass


class ClientAPI:
    def __init__(
        self, host=None, port=None, username=None, password=None, dataset=None, local_backend=None
    ):
        self.is_initialized = False

        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.dataset = dataset
        self.local_backend = local_backend

        # Set LOCAL_BACKEND
        # if settings.LOCAL_BACKEND:
        #     for ee_id, ee_info in self.runtime.ee_infos.items():
        #         if ee_info.sl_name == settings.LOCAL_BACKEND:
        #             global LOCAL
        #             LOCAL = ee_id
        #             break
        #     else:
        #         logger.warning(f"Backend with name '{settings.LOCAL_BACKEND}' not found, ignoring")

    def start(self):
        """Initialization made on the client-side, with .env settings

        Note that after a successful call to this method, subsequent calls will be
        a no-operation.
        """

        if self.is_initialized:
            logger.warning("Already initialized. Ignoring")
            return

        logger.info("Initializing client")

        self.old_settings_dict = settings.__dict__.copy()
        settings.load_client_properties(
            self.host, self.port, self.username, self.password, self.dataset, self.local_backend
        )

        self.old_runtime = get_runtime()
        self.runtime = ClientRuntime(
            settings.DATACLAY_METADATA_HOSTNAME, settings.DATACLAY_METADATA_PORT
        )
        set_runtime(self.runtime)

        # Create a new session
        self.session = self.runtime.metadata_service.new_session(
            settings.DC_USERNAME, settings.DC_PASSWORD, settings.DC_DATASET
        )
        self.runtime.session = self.session
        self.runtime.metadata_service.session = self.session

        # Cache the backends clients
        self.runtime.update_backend_clients()

        # Cache the dataclay_id, to avoid later request
        # self.runtime.dataclay_id

        logger.debug(f"Started session {self.session.id}")
        self.is_initialized = True

    def stop(self):
        if not self.is_initialized:
            logger.warning("Already finished. Ignoring")
            return

        logger.info("Finishing client API")
        self.runtime.stop()
        settings.__dict__.update(self.old_settings_dict)
        self.is_initialized = False

    def __del__(self):
        self.stop()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()

    def get_backends(self):
        self.runtime.update_backend_clients()
        return self.runtime.backend_clients


##########
# Dataclay
##########


def register_dataclay(id, hostname, port):
    """Register external dataClay for federation
    Args:
        hostname: external dataClay host name
        port: external dataClay port
    """
    return get_runtime().register_external_dataclay(id, hostname, port)


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
