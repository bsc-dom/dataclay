
""" Class description goes here. """

"""Settings for dataClay application.

All settings for dataClay are defined here. Values will be read from the module
specified by the DATACLAY_SETTINGS_MODULE environment variable, and then from
dataclay.conf.global_settings.

Note that this code has been heavily inspired by the Django's conf module.
"""
import logging
import os

from dataclay.commonruntime.SettingsLoader import AccountIdLoader, AccountCredentialLoader, AbstractLoader
from dataclay.exceptions.exceptions import ImproperlyConfigured
from dataclay.util.PropertiesFilesLoader import PropertyDict
from dataclay.util import Configuration

__author__ = 'Alex Barcelo <alex.barcelo@bsc.es>'
__copyright__ = '2015 Barcelona Supercomputing Center (BSC-CNS)'

logger = logging.getLogger(__name__)

# Fields for the main properties file
FIELD_ACCOUNT = "Account"
FIELD_PASSWORD = "Password"
FIELD_STUBSFOLDER = "StubsClasspath"
FIELD_DATASETS = "DataSets"
FIELD_DATASETFORSTORE = "DataSetForStore"
FIELD_CLIENTCONFIG = "DataClayClientConfig"
FIELD_GLOBALCONFIG = "DataClayGlobalConfig"
FIELD_LOCAL_BACKEND = "LocalBackend"
FIELD_TRACING_ENABLED = "Tracing"
FIELD_EXTRAE_STARTING_TASK_ID = "ExtraeStartingTaskID"
FIELD_PYCLAY_EXTRAE_WRAPPER_LIB = "pyClayExtraeWrapperLib"

# Fields for the client.properties file
FIELD_CLIENT_HOST = "HOST"
FIELD_CLIENT_TCPPORT = "TCPPORT"

UNSET_FIELD = object()


class _SettingsHub(object):
    """Application-wide configuration holder.

    This class holds values for all the configuration. It has some defaults,
    but a load from the properties file will overwrite the class values for
    specific instance values.

    Note that any lookup previous to a load_properties will raise an
    ImproperlyConfigured exception.
    """
    loaded = False

    def __init__(self):
        self.initialize()

    def initialize(self):
        # Ensure a instance copy of the global class-default dictionary
        self._values = {
            'logicmodule_host': "127.0.0.1",
            'logicmodule_port': "2127",
            'logicmodule_rmiport': "2127",
            'logicmodule_dc_instance_id': None,
            'network_timeout': 7200,

            'local_backend_name': None,

            'admin_user': os.getenv("DATACLAY_ADMIN_USER", "admin"),
            'admin_password': os.getenv("DATACLAY_ADMIN_PASSWORD", "admin"),
            'admin_id': AccountIdLoader(self, 'admin_user'),
            'admin_credential': AccountCredentialLoader(self, 'admin_id', 'admin_password'),

            'current_user': UNSET_FIELD,
            'current_password': UNSET_FIELD,
            'current_id': AccountIdLoader(self, 'current_user'),
            'current_credential': AccountCredentialLoader(self, 'current_id', 'current_password'),
            'current_session_id': UNSET_FIELD,

            'stubs_folder': UNSET_FIELD,

            'datasets': UNSET_FIELD,
            'dataset_for_store': UNSET_FIELD,
            'dataset_id': UNSET_FIELD,  # This is the DataSetID for the dataset_for_store

            # Tracing
            'tracing_enabled': False,
            'extrae_starting_task_id': "0",
            'pyclay_extrae_wrapper_lib': ""
        }

    def load_properties(self, file_name):
        """Load all the properties.

        Take a properties file and load all the settings used typically by the
        client application.
        """
        dirname = os.getcwd()

        d = PropertyDict(file_name)
        logger.debug("Reading properties file %s", file_name)

        try:
            self._values["current_user"] = getattr(d, FIELD_ACCOUNT)
            self._values["current_password"] = getattr(d, FIELD_PASSWORD)

            # Note to developers: The following os.path.join usage works because of:
            #   > (...) If a component is an absolute path, all previous components
            #   > are thrown away and joining continues from the absolute path component.

            # Ensure real path, just in case, regarding the properties' file
            self._values["stubs_folder"] = os.path.realpath(os.path.join(
                dirname, getattr(d, FIELD_STUBSFOLDER)))
            logger.debug("Stubs folder is %s", self._values["stubs_folder"])
            self._values["datasets"] = getattr(d, FIELD_DATASETS).split(':')
            self._values["dataset_for_store"] = getattr(d, FIELD_DATASETFORSTORE)

            try:
                self._values["extrae_starting_task_id"] = int(getattr(d, FIELD_EXTRAE_STARTING_TASK_ID))
            except AttributeError:
                logger.debug("Extrae starting task ID not defined")

            try:
                wrapper_lib = getattr(d, FIELD_PYCLAY_EXTRAE_WRAPPER_LIB)
                self._values["pyclay_extrae_wrapper_lib"] = wrapper_lib
            except AttributeError:
                logger.debug("dataClay Extrae Wrapper lib conf. not defined in session file")

                
                
            try:
                self._values["tracing_enabled"] = bool(getattr(d, FIELD_TRACING_ENABLED))
            except AttributeError:
                logger.debug("Tracing enabled conf. not defined")

            # Get relative to the path of the client configuration file, and clean up
            try:
                client_config_path = os.path.realpath(os.path.join(
                    dirname, getattr(d, FIELD_CLIENTCONFIG)))
            except AttributeError:
                client_config_path = os.getenv("DATACLAYCLIENTCONFIG")
                if not client_config_path:
                    client_config_path = os.path.realpath("./cfgfiles/client.properties")

            if not client_config_path:
                raise AttributeError("Client config cannot be found neither from session file nor any default env / path")
                        
            try:
                global_config_path = os.path.realpath(os.path.join(
                    dirname, getattr(d, FIELD_GLOBALCONFIG)))
                Configuration.read_from_file(global_config_path)
            except AttributeError:
                # not defined, ignore
                pass
            
        except AttributeError:
            logger.error("Some required attribute was missing, reraising the AttributeError")
            raise

        self.load_connection(client_config_path)

        # Last thing to do is establish the "LOCAL" backend
        if hasattr(d, FIELD_LOCAL_BACKEND):
            self._values["local_backend_name"] = getattr(d, FIELD_LOCAL_BACKEND)

    def load_connection(self, file_name):
        """Load the connection settings values.

        This method may be used standalone or called from the more complete
        load_properties.
        """
        client_d = PropertyDict(file_name)

        try:
            self._values["logicmodule_host"] = getattr(client_d, FIELD_CLIENT_HOST)
            self._values["logicmodule_port"] = int(getattr(client_d, FIELD_CLIENT_TCPPORT))
        except AttributeError:
            logger.error("CLIENTCONFIG file (typically client.properties) requires both %s and %p",
                         FIELD_CLIENT_HOST, FIELD_CLIENT_TCPPORT)
            raise

        # This method suffices for the load flag
        self.loaded = True

    def load_session_properties(self):
        self._values['METADATA_SERVICE_HOST'] = os.environ["METADATA_SERVICE_HOST"]
        self._values['METADATA_SERVICE_PORT'] = int(os.getenv("METADATA_SERVICE_PORT", "16587"))

        self._values['DC_USERNAME'] = os.environ["DC_USERNAME"]
        self._values['DC_PASSWORD'] = os.environ["DC_PASSWORD"]

        self._values['DATASETS'] = os.environ["DATASETS"].split(':')
        self._values['DATASET_FOR_STORE'] =os.environ["DATASET_FOR_STORE"]

        self.loaded = True


    def __getattr__(self, item):
        if not self.loaded:
            raise ImproperlyConfigured("The settings should be loaded before lookups")

        try:
            ret = self._values[item]
        except KeyError:
            raise ImproperlyConfigured("Key '%s' not recognized as a valid setting" % item)

        if ret is UNSET_FIELD:
            raise ImproperlyConfigured("The setting for '%s' has not been set" % item)

        if isinstance(ret, AbstractLoader):
            # if it is ready to be loaded, then load->store->return
            loaded = ret.load_value()
            self._values[item] = loaded
            return loaded
        else:
            return ret

    def __setattr__(self, key, value):
        if key == "loaded":
            object.__setattr__(self, key, value)
        elif key == "_values":
            # We expect that this is only done by the initialization
            object.__setattr__(self, key, value)
        else:
            self._values[key] = value

    def unload(self):
        logger.debug(f"[Settings] Unloading...")
        self.loaded = False
        self.initialize()



settings = _SettingsHub()

def unload_settings():
    global settings
    settings.unload()