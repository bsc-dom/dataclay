"""Common library client API for dataClay.

Runtime.
Note that importing this module has a basic semantic: it prepares the dataClay
core and sets the "client" mode for the library.
"""

__copyright__ = "2015 Barcelona Supercomputing Center (BSC-CNS)"
__all__ = ["init", "finish", "DataClayObject"]

import logging.config
import os
import warnings

from dataclay.communication.grpc.clients.LogicModuleGrpcClient import LMClient
from dataclay.dataclay_object import DataClayObject
from dataclay.paraver import (
    TRACE_ENABLED,
    extrae_tracing_is_enabled,
    get_task_id,
    set_current_available_task_id,
)
from dataclay.runtime import get_runtime, set_runtime, settings, unload_settings
from dataclay.runtime.client_runtime import ClientRuntime
from dataclay.runtime.client_runtime import UNDEFINED_LOCAL as _UNDEFINED_LOCAL
from dataclay.runtime.Initializer import _get_logging_dict_config, initialize
from opentelemetry import trace

# This will be populated during initialization
LOCAL = _UNDEFINED_LOCAL

tracer = trace.get_tracer(__name__)
logger = logging.getLogger("dataclay.api")

_connection_initialized = False
_initialized = False


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


def reinitialize_clients() -> None:
    raise
    """
    Reinitialize connection to logic module
    :return: None
    """
    runtime = get_runtime()
    logger.verbose(
        "Performing reinitialization of clients, removing #%d cached ones and recreating LMClient",
        len(runtime.backend_clients),
    )
    runtime.backend_clients = {
        "@LM": LMClient(settings.logicmodule_host, settings.logicmodule_port),
    }


# TODO: REFACTOR Remove this function. Currently used by tool/functions
def init_connection(client_file) -> LMClient:
    """Initialize the connection client ==> LogicModule.

    Note that the connection can be initialized standalone from here (like the
    dataClay tool performs) or it can be initialized by the full init() call.

    :param client_file: The path to the `client.properties` file. If set to None,
    then this function assumes that the connection settings are already loaded.
    :return: The LogicModule client (also accessible through the global
    commonruntime.backend_clients["@LM"]
    """
    global _connection_initialized
    logger.debug("Initializing dataClay connection with LM")

    settings.load_metadata_properties()
    runtime = ClientRuntime(settings.METADATA_SERVICE_HOST, settings.METADATA_SERVICE_PORT)
    set_runtime(runtime)

    if _connection_initialized:
        logger.warning("Runtime already has a client with the LogicModule, reusing that")
        return runtime.backend_clients["@LM"]

    client = LMClient(os.environ["LOGICMODULE_HOST"], os.getenv("LOGICMODULE_PORT_TCP", 11034))
    runtime.backend_clients["@LM"] = client

    _connection_initialized = True

    # TODO: Remove this call to LM
    # wait for 1 python backend
    # while len(get_backends_info()) < 1:
    #     logger.info("Waiting for any python backend to be ready ...")
    #     sleep(2)

    return client


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

        settings.load_metadata_properties()
        settings.load_session_properties()

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


# DEPRECATED: Remove this function
def post_network_init():
    raise
    global _initialized

    """Perform the last part of initialization, now with network."""
    client = init_connection(None)

    # Remember this function is called after a fork in workers also.
    # Activate Extrae if needed.
    ### READ ####
    # Activating tracing with tracing_enabled property set True and starting task id = 0 means we are only tracing dataClay
    # dataClay client will not increment current available task ID and will send a 0 to LM, which will understand the 0 as
    # "only dataClay tracing" since for compss it is never 0.
    # Activating tracing with tracing_enabled property set True and starting task id != 0 means we are tracing COMPSs
    # and dataClay. Current client will not initialize pyextrae or increment task id since COMPSs already initializes
    # it for us (as a worker).
    # In any case, none of them needs to add synchronization event or increment the available task id (only services).
    # Synchronization events are used to merge LM traces and python EE traces. Incrementing available task id is useful to
    # send to N EE/DS nodes.
    if settings.tracing_enabled:
        logger.info("Initializing tracing")

        extrae_compss = int(settings.extrae_starting_task_id) != 0

        if extrae_compss:
            get_runtime().activate_tracing(False)
            # set current available task id
            # set_current_available_task_id(int(settings.extrae_starting_task_id))
            # if get_task_id() == 0:
            #    get_runtime().activate_tracing_in_dataclay_services()

        else:
            get_runtime().activate_tracing(True)
            if get_task_id() == 0:
                get_runtime().activate_tracing_in_dataclay_services()

    # The new_session RPC may fall, and thus we will consider
    # the library as "not initialized". Arriving here means "all ok".
    _initialized = True


def finish_tracing():
    """
    Finishes tracing if needed
    """
    raise
    if extrae_tracing_is_enabled():
        extrae_compss = int(settings.extrae_starting_task_id) != 0

        if extrae_compss:
            if get_task_id() == 0:
                get_runtime().deactivate_tracing(False)
                # in compss Java runtime will get traces for us
            else:
                get_runtime().deactivate_tracing(False)

        else:
            if get_task_id() == 0:
                get_runtime().deactivate_tracing_in_dataclay_services()
                get_runtime().deactivate_tracing(True)
                get_runtime().get_traces_in_dataclay_services()  # not on workers!
                # Merge
                os.system("mpi2prv -keep-mpits -no-syn -f TRACE.mpits -o ./trace/dctrace.prv")
            else:
                get_runtime().deactivate_tracing(True)


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
        unload_settings()
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
