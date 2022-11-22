"""Common library client API for dataClay.

Runtime.
Note that importing this module has a basic semantic: it prepares the dataClay
core and sets the "client" mode for the library.
"""

__all__ = ["init", "finish", "DataClayObject"]

import logging.config
import warnings

from opentelemetry import trace

from dataclay.conf import settings
from dataclay.dataclay_object import DataClayObject
from dataclay.runtime import get_runtime, set_runtime
from dataclay.runtime.client_runtime import UNDEFINED_LOCAL as _UNDEFINED_LOCAL
from dataclay.runtime.client_runtime import ClientRuntime
from dataclay.runtime.Initializer import _get_logging_dict_config, initialize

# This will be populated during initialization
LOCAL = _UNDEFINED_LOCAL

tracer = trace.get_tracer(__name__)
logger = logging.getLogger("dataclay.api")

_connection_initialized = False
_initialized = False


# def client(username, password, etcd_ip,):
#     return DataclayClient()


def is_initialized() -> bool:
    """Simple query for the _initialized flag.

    :return: True if `init` has already been called, False otherwise.
    """
    return _initialized


def reinitialize_logging() -> None:
    """
    Restart logging system with new logging dict configuration
    :return: None
    """
    warnings.warn("deprecated", DeprecationWarning)
    dictconfig = _get_logging_dict_config()
    logger.debug("Ready to close loggers, bye bye!")
    dictconfig["disable_existing_loggers"] = False
    logging.config.dictConfig(dictconfig)
    logger.verbose("Logging reinitialized. Welcome back!")


###############
# Backends info
###############


def get_backends():
    """Return all the dataClay backend present in the system."""
    result = get_runtime().get_execution_environments_names()
    logger.debug("Got %i python backend/s", len(result))
    return result


def get_backends_info():
    """Return all the dataClay BackendInfo present in the system."""
    get_runtime().update_ee_infos()
    result = get_runtime().ee_infos
    logger.debug(f"Got {len(result)} python backend/s")
    return result


def get_backend_id_by_name(name):
    """Return dataClay backend present in the system with name provided."""
    all_backends = get_runtime().get_all_execution_environments_with_name(name)
    for backend in all_backends.values():
        if backend.sl_name == name:
            return backend.id
    return None


def get_external_backend_id_by_name(name, external_dataclay_id):
    """Return dataClay backend present in the system with name provided."""
    all_backends = get_runtime().get_all_execution_environments_at_dataclay(external_dataclay_id)
    for backend in all_backends.values():
        if backend.sl_name == name:
            return backend.id
    return None


def get_backend_id(hostname, port):
    """Return dataClay backend present in the system with name provided."""
    host_ee_infos = get_runtime().get_all_execution_environments_at_host(hostname)
    for backend in host_ee_infos.values():
        if backend.port == port:
            return backend.id
    return None


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


def get_dataclay_id():
    """Get dataClay ID"""
    return get_runtime().dataclay_id


def import_models_from_external_dataclay(namespace, ext_dataclay_id) -> None:
    """Import models in namespace specified from an external dataClay
    :param namespace: external dataClay namespace to get
    :param ext_dataclay_id: external dataClay ID
    :return: None
    :type namespace: string
    :type ext_dataclay_id: UUID
    :rtype: None
    """
    return get_runtime().import_models_from_external_dataclay(namespace, ext_dataclay_id)


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


# TODO: Structure in smaller functions
def init():
    """Initialization made on the client-side, with .env settings

    Note that after a successful call to this method, subsequent calls will be
    a no-operation.
    """

    with tracer.start_as_current_span("init") as init_span:

        logger.info("Initializing dataClay API")

        # Checks if dataclay is already initialized
        global _initialized
        if _initialized:
            logger.warning("Already initialized --ignoring")
            return

        settings.load_client_properties()

        # Initialize ClientRuntime
        runtime = ClientRuntime(settings.METADATA_SERVICE_HOST, settings.METADATA_SERVICE_PORT)
        set_runtime(runtime)

        # TODO: Do we need it for federation?
        # Get dataclay id and map it to Metadata Service client
        # runtime.backend_clients[runtime.metadata_service.get_dataclay_id()] = client

        # wait for 1 python backend
        # TODO: implement get_backends_info in MDS
        # while len(get_backends_info()) < 1:
        #     logger.info("Waiting for any python backend to be ready ...")
        #     sleep(2)

        # Create a new session
        session = runtime.metadata_service.new_session(
            settings.DC_USERNAME, settings.DC_PASSWORD, settings.DEFAULT_DATASET
        )
        runtime.session = session

        init_span.add_event("marcevent - after new session")

        # Cache the execution environment infos
        runtime.update_backend_clients()

        # Cache the dataclay_id, to avoid later request
        runtime.dataclay_id

        # Set LOCAL_BACKEND
        if settings.LOCAL_BACKEND:
            for ee_id, ee_info in runtime.ee_infos.items():
                if ee_info.sl_name == settings.LOCAL_BACKEND:
                    global LOCAL
                    LOCAL = ee_id
                    break
            else:
                logger.warning(f"Backend with name '{settings.LOCAL_BACKEND}' not found, ignoring")

        _initialized = True
        logger.debug(f"Started session {session.id}")

        init_span.add_event("marcevent - ending init")


def finish():
    with tracer.start_as_current_span("finish") as span:
        global _initialized
        if not _initialized:
            logger.warning("Already finished --ignoring")
            return
        global _connection_initialized
        logger.info("Finishing dataClay API")
        # finish_tracing()
        get_runtime().close_session()
        get_runtime().stop_runtime()

        # unload settings
        # unload_settings()
        _initialized = False
        _connection_initialized = False


######################################
# Static initialization of dataClay
##########################################################

# The client should never need the delete methods of persistent objects
# ... not doing this is a performance hit
# del DataClayObject.__del__


initialize()


# Now the logger is ready
logger.verbose("Client-mode initialized, dataclay.commonruntime should be ready")
