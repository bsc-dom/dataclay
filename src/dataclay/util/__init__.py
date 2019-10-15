
""" Class description goes here. """

from datetime import datetime
from dataclay.util.ConfigurationFlags import ConfigurationFlags
import logging
import os
import traceback
logger = logging.getLogger('dataclay.api')


class Configuration(object):
    """Configuration management static-ish class."""

    DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"

    # Session control
    ########################
    CHECK_SESSION = False

    # Garbage collector
    ########################

    # Percentage to start flushing objects
    MEMMGMT_PRESSURE_FRACTION = 0.75

    # Percentage to stop flushing objects
    MEMMGMT_EASE_FRACTION = 0.50

    # Number of milliseconds to check if Heap needs to be cleaned.
    MEMMGMT_CHECK_TIME_INTERVAL = 5000

    # Global GC collection interval
    NOCHECK_SESSION_EXPIRATION = datetime.strptime('2120-09-10T20:00:04', DATE_FORMAT)

    # ====================== TIME OUTS AND RETRIES ========================== #

    # NEW DATA-SERVICE OR EXECUTION ENVIRONMENT: WARNING: for each retry there is max_retries_logicmodule
    # Maximum autoregistration retries of a node. 
    MAX_RETRY_AUTOREGISTER = 10
    # Seconds to wait to retry autoregistration of a node. 
    RETRY_AUTOREGISTER_TIME = 3000
        
    # ANY CALL TO LOGICMODULE: clients can wait at init waitForBackends
    # Default value for number of retries in connection to LogicModule. 
    MAX_RETRIES_LOGICMODULE = 1
    # Default value for sleeping before retrying in LM in millis. 
    SLEEP_RETRIES_LOGICMODULE = 100
        
    # EXECUTION RETRIES
    # Default value for number of retries IN EXECUTION
    MAX_EXECUTION_RETRIES = 5
        
    # WAIT FOR OBJECTS TO BE REGISTERED BY GC
    # Number of millis of time to wait for object to be registered. Default: NO WAIT 
    TIMEOUT_WAIT_REGISTERED = 0  # fixme do we need this?
    # Waiting milliseconds to check if object to be registered. 
    SLEEP_WAIT_REGISTERED = 50
    
    # CHECK ALIVE TIME OUT IN GRPC in seconds
    GRPC_CHECK_ALIVE_TIMEOUT = 3
    
    # Indicates where EE id is stored
    EE_PERSISTENT_INFO_PATH = os.getcwd() + "/"

    # How many worker threads should be created/used by ThreadPoolExecutor
    THREAD_POOL_WORKERS = 2

    # Path to Trusted certificates for verifying the remote endpoint's certificate. 
    SSL_CLIENT_TRUSTED_CERTIFICATES = ""

    # Path to identifying certificate for this host
    SSL_CLIENT_CERTIFICATE = ""

    # Path to identifying certificate for this host. 
    SSL_CLIENT_KEY = ""
    
    # Custom header of service alias for calls to Logic module. Used in Traefik.
    LM_SERVICE_ALIAS_HEADERMSG = "logicmodule1"
    
    # Override authority hostname in SSL calls
    SSL_TARGET_AUTHORITY = "proxy"

    @classmethod
    def read_from_file(cls, flags_path):
        
        # Check if environment variable is set 
        abs_flags_path = os.path.abspath(flags_path)
        print("--- Using global.properties at %s" % abs_flags_path)
        try:
            flags = ConfigurationFlags(property_path=abs_flags_path)
            globalattrs = [a for a in dir(flags) if not a.startswith('__')]
            for attr in globalattrs:
                value = getattr(flags, attr)
                if hasattr(cls, attr):
                    cur_value = getattr(cls, attr)
                    print("Found global.properties variable %s=%s and type %s" % (str(attr), str(value), str(type(cur_value))))
                    setattr(cls, str(attr), type(cur_value)(value))

        except:
            print("No global.properties file found. Using default values")


# Check if environment variable is set 
if "DATACLAYGLOBALCONFIG" in os.environ:
    flags_path = os.environ["DATACLAYGLOBALCONFIG"]
else:
    flags_path = "./cfgfiles/global.properties"
    
Configuration.read_from_file(flags_path)
