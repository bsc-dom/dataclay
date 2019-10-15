
""" Class description goes here. """

import os
import logging
from dataclay.commonruntime.Settings import settings

__author__ = 'Alex Barcelo <alex.barcelo@bsc.es>'
__copyright__ = '2015 Barcelona Supercomputing Center (BSC-CNS)'
logger = logging.getLogger(__name__)


def set_defaults():
    # extrae
    settings.tracing_enabled = False
    settings.extrae_starting_task_id = 0

    # Firewall it if this listen address is not advisable
    settings.server_listen_addr = "0.0.0.0"

    port_str = os.getenv("DATASERVICE_PYTHON_PORT_TCP", "6867")
    settings.server_listen_port = int(port_str)

    settings.pool_size = 4
    settings.interpreter_pool = None

    settings.cached_objects_size = 100
    settings.cached_classes_size = 1000
    settings.cached_metaclasses_size = 1000
    settings.cached_metaclass_info_size = 1000

    settings.cache_on_deploy = True

    # ToDo: This is a dangerous default, used in Docker but... useless everywhere else.
        
    deploy_path = os.getenv("DEPLOY_PATH", "/usr/src/app/deploy")
    settings.deploy_path = deploy_path
    settings.deploy_path_source = os.getenv("DEPLOY_PATH_SRC",
                                            os.path.join(deploy_path, "source"))
    # Retain the IDs associated to this server
    settings.storage_id = None  # The Java, which is both StorageLocation and Java ExecutionEnvironment
    settings.environment_id = None  # This is (should be) ourselves

    ###########################################################################
    # The following is the "published" information for the autoregister RPC
    settings.dataservice_name = os.getenv("DATASERVICE_NAME")
    # If there are no firewalls or strange stuff with ports,
    # the following is expected to match DATASERVICE_PYTHON_PORT_TCP
    # (the port the server listens to)
    settings.dataservice_port = int(os.getenv("DATASERVICE_PYTHON_PORT_TCP", port_str))
    #                                                                         #
    ###########################################################################

    settings.logicmodule_host = os.getenv("LOGICMODULE_HOST", "127.0.0.1")
    settings.logicmodule_rmiport = int(os.getenv("LOGICMODULE_PORT_RMI", "1024"))
    settings.logicmodule_port = int(os.getenv("LOGICMODULE_PORT_TCP", "1034"))

    # Setting defaults is considered loading settings
    settings.loaded = True
