"""
    Common library client API for dataClay.
    ~~~~~~~~~~~~~~

    Runtime.
    Note that importing this module has a basic semantic: it prepares the dataClay
    core and sets the "client" mode for the library.

    :copyright: (c) 2018 Barcelona Supercomputing Center
    :license: BSD-2
"""
import logging.config
import os.path
import sys

from dataclay import getRuntime
from dataclay.DataClayObject import DataClayObject
from dataclay.commonruntime.ClientRuntime import *
from dataclay.commonruntime.ClientRuntime import UNDEFINED_LOCAL as _UNDEFINED_LOCAL
from dataclay.commonruntime.Initializer import initialize, _get_logging_dict_config
from dataclay.communication.grpc.clients.LogicModuleGrpcClient import LMClient
from dataclay.paraver import TRACE_ENABLED, extrae_tracing_is_enabled, get_task_id, \
    set_current_available_task_id
from dataclay.util.StubUtils import track_local_available_classes
from time import sleep

# This will be populated during initialization
LOCAL = _UNDEFINED_LOCAL

__copyright__ = '2015 Barcelona Supercomputing Center (BSC-CNS)'
__all__ = ["init", "finish", "DataClayObject"]
logger = logging.getLogger('dataclay.api')
_connection_initialized = False
_initialized = False


def is_initialized():
    """Simple query for the _initialized flag.

    :return: True if `init` has already been called, False otherwise.
    """
    return _initialized


def reinitialize_logging():
    dictconfig = _get_logging_dict_config()

    logger.debug("Ready to close loggers, bye bye!")
    dictconfig["disable_existing_loggers"] = False
    logging.config.dictConfig(dictconfig)
    logger.verbose("Logging reinitialized. Welcome back!")


def reinitialize_clients():
    runtime = getRuntime()
    logger.verbose("Performing reinitialization of clients, removing #%d cached ones and recreating LMClient",
                len(runtime.ready_clients))
    runtime.ready_clients = {
        "@LM": LMClient(settings.logicmodule_host, settings.logicmodule_port),
    }


def init_connection(client_file):
    """Initialize the connection client ==> LogicModule.

    Note that the connection can be initialized standalone from here (like the
    dataClay tool performs) or it can be initialized by the full init() call.

    :param client_file: The path to the `client.properties` file. If set to None,
    then this function assumes that the connection settings are already loaded.
    :return: The LogicModule client (also accessible through the global
    commonruntime.ready_clients["@LM"]
    """
    global _connection_initialized
    logger.verbose("Initializing dataClay connection with LM")
    runtime = getRuntime()
    if _connection_initialized:
        logger.warning("Runtime already has a client with the LogicModule, reusing that")
        return runtime.ready_clients["@LM"]

    if client_file:
        settings.load_connection(client_file)

    # Once the properties are load, we can prepare the LM client
    logger.verbose("Initializing dataClay connection with LM %s:%s", settings.logicmodule_host, settings.logicmodule_port)
    client = LMClient(settings.logicmodule_host, settings.logicmodule_port)
    runtime.ready_clients["@LM"] = client
    
    _connection_initialized = True

    settings.logicmodule_dc_instance_id = client.get_dataclay_id()

    logger.verbose("DataclayInstanceID is %s, storing client in cache", settings.logicmodule_dc_instance_id)
    runtime.ready_clients[settings.logicmodule_dc_instance_id] = runtime.ready_clients["@LM"]

    # wait for 1 python backend 
    while len(get_backends()) < 1:
        logger.info("Waiting for any python backend to be ready ...")
        sleep(2)

    return client


def get_backends():
    """Return all the dataClay backend present in the system."""
    result = getRuntime().get_execution_environments_names("admin", "admin")
    logger.debug("Got %i python backend/s", len(result))
    return result


def get_backends_info():
    """Return all the dataClay BackendInfo present in the system."""
    result = getRuntime().get_execution_environments_info()
    logger.debug("Got %i python backend/s", len(result))
    return result


def get_backend_id_by_name(name):
    """Return dataClay backend present in the system with name provided."""
    all_backends = getRuntime().get_execution_environments_info()
    for backend in all_backends.values():
        if backend.name == name:
            return backend.dataClayID
    return None


def register_external_dataclay(exthostname, extport):
    """ Register external dataClay for federation
    :param exthostname: external dataClay host name
    :param extport: external dataClay port
    :return: external dataClay ID registered
    :type exthostname: string
    :type extport: int
    :rtype: UUID
    """
    return getRuntime().register_external_dataclay(exthostname, extport)


def get_external_dataclay_id(exthostname, extport):
    """ Get external dataClay ID with host and port identified
    :param exthostname: external dataClay host name
    :param extport: external dataClay port
    :return: None
    :type exthostname: string
    :type extport: int
    :rtype: None
    """
    return getRuntime().get_external_dataclay_id(exthostname, extport)


def unfederate_all_objects(ext_dataclay_id):
    """ Unfederate all objects belonging/federated with external data clay with id provided
    :param ext_dataclay_id: external dataClay id
    :return: None
    :type ext_dataclay_id: uuid
    :rtype: None
    """
    return getRuntime().unfederate_all_objects(ext_dataclay_id)


def unfederate_all_objects_with_all_dcs():
    """ Unfederate all objects belonging/federated with ANY external data clay
    :return: None
    :rtype: None
    """
    return getRuntime().unfederate_all_objects_with_all_dcs()


def migrate_federated_objects(origin_dataclay_id, dest_dataclay_id):
    """ Migrate federated objects from origin dataclay to destination dataclay
    :param origin_dataclay_id: origin dataclay id 
    :param dest_dataclay_id destination dataclay id
    :return: None
    :rtype: None
    """
    return getRuntime().migrate_federated_objects(origin_dataclay_id, dest_dataclay_id)


def federate_all_objects(dest_dataclay_id):
    """ Federate all objects from current dataclay to destination dataclay
    :param dest_dataclay_id destination dataclay id
    :return: None
    :rtype: None
    """
    return getRuntime().federate_all_objects(dest_dataclay_id)


def pre_network_init(config_file):
    """Perform a partial initialization, with no network."""
    settings.load_properties(config_file)


def init(config_file="./cfgfiles/session.properties"):
    """Initialization made on the client-side, with file-based settings.

    Note that after a successful call to this method, subsequent calls will be
    a no-operation.

    :param config_file: The configuration file that will be used. If explicitly
    set to null, then its value will be retrieved from the DATACLAYSESSIONCONFIG
    environment variable.
    """
    global _initialized

    logger.info("Initializing dataClay API")

    if _initialized:
        logger.warning("Already initialized --ignoring")
        return

    if (not config_file) or (not os.path.isfile(config_file)):
        # Fallback when either
        #   - init has been called explicitly with falsy value
        #   - the default file does not exist
        config_file = os.getenv("DATACLAYSESSIONCONFIG")
        if not config_file:
            raise ValueError("dataClay requires a session.properties in order to initialize")

    pre_network_init(config_file)
    post_network_init()


def post_network_init():
    global _initialized

    """Perform the last part of initialization, now with network."""
    client = init_connection(None)

    # In all cases, track (done through babelstubs YAML file)
    contracts = track_local_available_classes()

    # Ensure they are in the path (high "priority")
    sys.path.insert(0, os.path.join(settings.stubs_folder, 'sources'))

    if not contracts:
        logger.warning("No contracts available. Calling new_session, but no classes will be available")

    """ Initialize runtime """
    getRuntime().initialize_runtime()

    session_info = client.new_session(
        settings.current_id,
        settings.current_credential,
        contracts,
        [client.get_dataset_id(settings.current_id, settings.current_credential, dataset) for dataset in settings.datasets],
        client.get_dataset_id(settings.current_id, settings.current_credential, settings.dataset_for_store),
        LANG_PYTHON
    )
    settings.current_session_id = session_info.sessionID

    name = settings.local_backend_name
    if name:
        exec_envs = getRuntime().get_execution_environments_info()
        for k, v in exec_envs.items():
            if exec_envs[k].name == name:
                global LOCAL
                LOCAL = k
                break
        else:
            logger.warning("Backend with name '%s' not found, ignoring", name)

    settings.dataset_id = client.get_dataset_id(
        settings.current_id,
        settings.current_credential,
        settings.dataset_for_store)

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
        # set current available task id 
        set_current_available_task_id(int(settings.extrae_starting_task_id)) 
        # -- Do NOT add synchronization events if it is a compss worker (default case of activation) --
        getRuntime().activate_tracing()
        # TODO: check if is in master, should always be master since initWorker is the one called from workers only?
        # Fallback: if services have tracing active, the call is ignored
        getRuntime().activate_tracing_in_dataclay_services()

    # The new_session RPC may fall, and thus we will consider
    # the library as "not initialized". Arriving here means "all ok".
    _initialized = True


def finish_tracing():
    """
    Finishes tracing if needed 
    """
    if extrae_tracing_is_enabled():
        if int(settings.extrae_starting_task_id) == 0:  # in compss Java runtime will get traces for us
            getRuntime().deactivate_tracing_in_dataclay_services()
            getRuntime().deactivate_tracing()
            getRuntime().get_traces_in_dataclay_services()  # not on workers!
        else:
            getRuntime().deactivate_tracing()

            
def finish():
    global _initialized
    logger.info("Finishing dataClay API")
    finish_tracing()
    getRuntime().stop_runtime()
    _initialized = False

######################################
# Static initialization of dataClay
##########################################################

# The client should never need the delete methods of persistent objects
# ... not doing this is a performance hit
# del DataClayObject.__del__


initialize()


# Now the logger is ready
logger.verbose("Client-mode initialized, dataclay.commonruntime should be ready")
