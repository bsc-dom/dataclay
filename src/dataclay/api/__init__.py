"""Common library client API for dataClay.

Runtime.
Note that importing this module has a basic semantic: it prepares the dataClay
core and sets the "client" mode for the library.
"""
import logging.config
import os
import sys
import warnings


from dataclay import getRuntime
from dataclay.DataClayObject import DataClayObject
from dataclay.commonruntime.ClientRuntime import settings, LANG_PYTHON
from dataclay.commonruntime.ClientRuntime import UNDEFINED_LOCAL as _UNDEFINED_LOCAL
from dataclay.commonruntime.Initializer import initialize, _get_logging_dict_config
from dataclay.communication.grpc.clients.LogicModuleGrpcClient import LMClient
from dataclay.paraver import (
    TRACE_ENABLED,
    extrae_tracing_is_enabled,
    get_task_id,
    set_current_available_task_id,
)
from dataclay.util.StubUtils import track_local_available_classes
from dataclay.util.StubUtils import clean_babel_data
from dataclay.commonruntime.Settings import unload_settings

from dataclay_common.clients.metadata_service_client import MDSClient

from time import sleep

# This will be populated during initialization
LOCAL = _UNDEFINED_LOCAL

__copyright__ = "2015 Barcelona Supercomputing Center (BSC-CNS)"
__all__ = ["init", "finish", "DataClayObject"]
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
    """
    Reinitialize connection to logic module
    :return: None
    """
    runtime = getRuntime()
    logger.verbose(
        "Performing reinitialization of clients, removing #%d cached ones and recreating LMClient",
        len(runtime.ready_clients),
    )
    runtime.ready_clients = {
        "@LM": LMClient(settings.logicmodule_host, settings.logicmodule_port),
    }


# TODO: Remove this function
def init_connection(client_file) -> LMClient:
    """Initialize the connection client ==> LogicModule.

    Note that the connection can be initialized standalone from here (like the
    dataClay tool performs) or it can be initialized by the full init() call.

    :param client_file: The path to the `client.properties` file. If set to None,
    then this function assumes that the connection settings are already loaded.
    :return: The LogicModule client (also accessible through the global
    commonruntime.ready_clients["@LM"]
    """
    global _connection_initialized
    logger.debug("Initializing dataClay connection with LM")
    runtime = getRuntime()
    if _connection_initialized:
        logger.warning("Runtime already has a client with the LogicModule, reusing that")
        return runtime.ready_clients["@LM"]

    if client_file:
        settings.load_connection(client_file)

    # Once the properties are load, we can prepare the LM client
    logger.debug(
        "Initializing dataClay connection with LM %s:%s",
        settings.logicmodule_host,
        settings.logicmodule_port,
    )
    client = LMClient(settings.logicmodule_host, settings.logicmodule_port)
    runtime.ready_clients["@LM"] = client

    _connection_initialized = True

    # TODO: Remove this setting, and use metadata service id
    # settings.logicmodule_dc_instance_id = client.get_dataclay_id()

    logger.debug(
        "DataclayInstanceID is %s, storing client in cache", settings.logicmodule_dc_instance_id
    )
    runtime.ready_clients[settings.logicmodule_dc_instance_id] = runtime.ready_clients["@LM"]

    # TODO: Remove this call to LM
    # wait for 1 python backend
    # while len(get_backends_info()) < 1:
    #     logger.info("Waiting for any python backend to be ready ...")
    #     sleep(2)

    return client


def get_backends():
    """Return all the dataClay backend present in the system."""
    result = getRuntime().get_execution_environments_names(force_update=True)
    logger.debug("Got %i python backend/s", len(result))
    return result


def get_backends_info():
    """Return all the dataClay BackendInfo present in the system."""
    result = getRuntime().get_all_execution_environments_info(force_update=True)
    logger.debug("Got %i python backend/s", len(result))
    return result


def get_backend_id_by_name(name):
    """Return dataClay backend present in the system with name provided."""
    all_backends = getRuntime().get_all_execution_environments_with_name(name)
    for backend in all_backends.values():
        if backend.name == name:
            return backend.id
    return None


def get_external_backend_id_by_name(name, external_dataclay_id):
    """Return dataClay backend present in the system with name provided."""
    all_backends = getRuntime().get_all_execution_environments_at_dataclay(external_dataclay_id)
    for backend in all_backends.values():
        if backend.name == name:
            return backend.id
    return None


def get_backend_id(hostname, port):
    """Return dataClay backend present in the system with name provided."""
    all_backends = getRuntime().get_all_execution_environments_info(force_update=True)
    for backend in all_backends.values():
        if backend.hostname == hostname and backend.port == port:
            return backend.id
    return None


def register_dataclay(exthostname, extport):
    """Register external dataClay for federation
    :param exthostname: external dataClay host name
    :param extport: external dataClay port
    :return: external dataClay ID registered
    :type exthostname: string
    :type extport: int
    :rtype: UUID
    """
    return getRuntime().register_external_dataclay(exthostname, extport)


def get_dataclay_id(exthostname, extport):
    """Get external dataClay ID with host and port identified
    :param exthostname: external dataClay host name
    :param extport: external dataClay port
    :return: None
    :type exthostname: string
    :type extport: int
    :rtype: None
    """
    return getRuntime().get_external_dataclay_id(exthostname, extport)


def import_models_from_external_dataclay(namespace, ext_dataclay_id) -> None:
    """Import models in namespace specified from an external dataClay
    :param namespace: external dataClay namespace to get
    :param ext_dataclay_id: external dataClay ID
    :return: None
    :type namespace: string
    :type ext_dataclay_id: UUID
    :rtype: None
    """
    return getRuntime().import_models_from_external_dataclay(namespace, ext_dataclay_id)


def unfederate(ext_dataclay_id=None):
    """Unfederate all objects belonging to/federated with external data clay with id provided
    or with all any external dataclay if no argument provided.
    :param ext_dataclay_id: external dataClay id
    :return: None
    :type ext_dataclay_id: uuid
    :rtype: None
    """
    if ext_dataclay_id is not None:
        return getRuntime().unfederate_all_objects(ext_dataclay_id)
    else:
        return getRuntime().unfederate_all_objects_with_all_dcs()


def migrate_federated_objects(origin_dataclay_id, dest_dataclay_id):
    """Migrate federated objects from origin dataclay to destination dataclay
    :param origin_dataclay_id: origin dataclay id
    :param dest_dataclay_id destination dataclay id
    :return: None
    :rtype: None
    """
    return getRuntime().migrate_federated_objects(origin_dataclay_id, dest_dataclay_id)


def federate_all_objects(dest_dataclay_id):
    """Federate all objects from current dataclay to destination dataclay
    :param dest_dataclay_id destination dataclay id
    :return: None
    :rtype: None
    """
    return getRuntime().federate_all_objects(dest_dataclay_id)


def get_num_objects():
    """Get number of objects in dataClay
    :return: number of objects in dataClay
    :rtype: int32
    """
    return getRuntime().get_num_objects()


# TODO: Remove this function
def pre_network_init(config_file):
    """Perform a partial initialization, with no network."""
    settings.load_properties(config_file)


def mds_init():
    """ "Init that will replace current one for Metadata Service"""
    logger.info("Initializing dataClay API")

    settings.load_session_properties()

    # Create MDS Client and store it in a persistent way
    client = MDSClient(settings.METADATA_SERVICE_HOST, settings.METADATA_SERVICE_PORT)
    runtime = getRuntime()
    runtime.ready_clients["@MDS"] = client

    # Get dataclay id and map it to Metadata Service client
    # TODO: Rename setting to a more meaningfull name
    #       like metadata_id, dataclay_id, etc.
    settings.logicmodule_dc_instance_id = client.get_dataclay_id()
    runtime.ready_clients[settings.logicmodule_dc_instance_id] = client

    # wait for 1 python backend
    # TODO: implement get_backends_info in MDS
    # while len(get_backends_info()) < 1:
    #     logger.info("Waiting for any python backend to be ready ...")
    #     sleep(2)

    # Create a new session
    session_id = client.new_session(
        settings.DC_USERNAME, settings.DC_PASSWORD, settings.DEFAULT_DATASET
    )
    settings.current_session_id = session_id

    # Ensure they are in the path (high "priority")
    sys.path.insert(0, os.path.join(settings.stubs_folder, "sources"))

    logger.debug(f"Started session {session_id}")


def init(config_file=None) -> None:
    """Initialization made on the client-side, with file-based settings.

    Note that after a successful call to this method, subsequent calls will be
    a no-operation.

    :param config_file: The configuration file that will be used. If not set, then
     the DATACLAYSESSIONCONFIG environment variable will be used and the fallback
     will be the `./cfgfiles/session.properties` path.
    """

    # TODO: Use replace init(..) to mds_init(..)

    global _initialized

    logger.info("Initializing dataClay API")

    if _initialized:
        logger.warning("Already initialized --ignoring")
        return

    if not config_file:
        # If the call doesn't has config_file set, let's try to fallback into the envvar
        env_config_file = os.getenv("DATACLAYSESSIONCONFIG")
        if env_config_file:
            # If the environment is defined, it is preferred
            config_file = env_config_file
            logger.info("Using the environment variable DATACLAYSESSIONCONFIG=%s", config_file)
        else:
            config_file = "./cfgfiles/session.properties"
            logger.info("Fallback to default ./cfgfiles/session.properties")
    else:
        logger.info('Explicit parameter config_file="%s" will be used', config_file)

    if not os.path.isfile(config_file):
        raise ValueError("dataClay requires a session.properties in order to initialize")

    pre_network_init(config_file)
    post_network_init()

    mds_init()


# TODO: Remove this function
def post_network_init():
    global _initialized

    """Perform the last part of initialization, now with network."""
    client = init_connection(None)

    # In all cases, track (done through babelstubs YAML file)
    contracts = track_local_available_classes()

    if not contracts:
        logger.warning(
            "No contracts available. Calling new_session, but no classes will be available"
        )

    """ Initialize runtime """
    getRuntime().initialize_runtime()

    name = settings.local_backend_name
    if name:
        exec_envs = getRuntime().get_all_execution_environments_info()
        for k, v in exec_envs.items():
            if exec_envs[k].name == name:
                global LOCAL
                LOCAL = k
                break
        else:
            logger.warning("Backend with name '%s' not found, ignoring", name)

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
            getRuntime().activate_tracing(False)
            # set current available task id
            # set_current_available_task_id(int(settings.extrae_starting_task_id))
            # if get_task_id() == 0:
            #    getRuntime().activate_tracing_in_dataclay_services()

        else:
            getRuntime().activate_tracing(True)
            if get_task_id() == 0:
                getRuntime().activate_tracing_in_dataclay_services()

    # The new_session RPC may fall, and thus we will consider
    # the library as "not initialized". Arriving here means "all ok".
    _initialized = True


def finish_tracing():
    """
    Finishes tracing if needed
    """
    if extrae_tracing_is_enabled():
        extrae_compss = int(settings.extrae_starting_task_id) != 0

        if extrae_compss:
            if get_task_id() == 0:
                getRuntime().deactivate_tracing(False)
                # in compss Java runtime will get traces for us
            else:
                getRuntime().deactivate_tracing(False)

        else:
            if get_task_id() == 0:
                getRuntime().deactivate_tracing_in_dataclay_services()
                getRuntime().deactivate_tracing(True)
                getRuntime().get_traces_in_dataclay_services()  # not on workers!
                # Merge
                os.system("mpi2prv -keep-mpits -no-syn -f TRACE.mpits -o ./trace/dctrace.prv")
            else:
                getRuntime().deactivate_tracing(True)


def finish():
    global _initialized
    if not _initialized:
        logger.warning("Already finished --ignoring")
        return
    global _connection_initialized
    logger.info("Finishing dataClay API")
    finish_tracing()
    getRuntime().close_session()
    logger.debug(f"Closed session {settings.current_session_id}")
    getRuntime().stop_runtime()
    # Unload stubs
    clean_babel_data()
    sys.path.remove(os.path.join(settings.stubs_folder, "sources"))
    # unload caches of stubs
    from dataclay.commonruntime.ExecutionGateway import (
        loaded_classes,
        class_extradata_cache_client,
        class_extradata_cache_exec_env,
    )

    loaded_classes.clear()
    class_extradata_cache_exec_env.clear()
    class_extradata_cache_client.clear()
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
