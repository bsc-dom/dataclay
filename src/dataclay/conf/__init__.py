import logging
import os
import socket
from datetime import datetime

logger = logging.getLogger(__name__)


class Settings:

    #####################
    # Garbage collector #
    #####################

    DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"

    CHECK_SESSION = False

    # Percentage to start flushing objects
    MEMMGMT_PRESSURE_FRACTION = float(os.getenv("MEMMGMT_PRESSURE_FRACTION", default=0.75))

    # Percentage to stop flushing objects
    MEMMGMT_EASE_FRACTION = float(os.getenv("MEMMGMT_PRESSURE_FRACTION", default=0.50))

    # Number of milliseconds to check if Heap needs to be cleaned.
    MEMMGMT_CHECK_TIME_INTERVAL = int(os.getenv("MEMMGMT_CHECK_TIME_INTERVAL", default=5000))

    # Global GC collection interval
    NOCHECK_SESSION_EXPIRATION = datetime.strptime("2120-09-10T20:00:04", DATE_FORMAT)

    #########################
    # Time outs and retries #
    #########################

    # Number of seconds to wait for grpc channel to be ready
    TIMEOUT_CHANNEL_READY = 5

    # MAX_RETRY_AUTOREGISTER = int(os.getenv("MAX_RETRY_AUTOREGISTER", default=80))

    # RETRY_AUTOREGISTER_TIME = int(os.getenv("RETRY_AUTOREGISTER_TIME", default=5000))

    # Default value for number of retries IN EXECUTION
    # MAX_EXECUTION_RETRIES = 5

    # Number of millis of time to wait for object to be registered. Default: NO WAIT
    # TIMEOUT_WAIT_REGISTERED = 0  # fixme do we need this?

    # Waiting milliseconds to check if object to be registered.
    # SLEEP_WAIT_REGISTERED = 50

    ########
    # gRPC #
    ########

    # CHECK ALIVE TIME OUT IN GRPC in seconds
    GRPC_CHECK_ALIVE_TIMEOUT = int(os.getenv("GRPC_CHECK_ALIVE_TIMEOUT", default=60))

    # Path to Trusted certificates for verifying the remote endpoint's certificate.
    SSL_CLIENT_TRUSTED_CERTIFICATES = os.getenv("SSL_CLIENT_TRUSTED_CERTIFICATES", default="")

    # Path to identifying certificate for this host
    SSL_CLIENT_CERTIFICATE = os.getenv("SSL_CLIENT_CERTIFICATE", default="")

    # Path to identifying certificate for this host.
    SSL_CLIENT_KEY = os.getenv("SSL_CLIENT_KEY", default="")

    # Override authority hostname in SSL calls
    SSL_TARGET_AUTHORITY = os.getenv("SSL_TARGET_AUTHORITY", default="proxy")

    # Custom header of service alias for calls to EE. Used in Traefik.
    SSL_TARGET_EE_ALIAS = os.getenv("SSL_TARGET_EE_ALIAS", default="6867")

    #########
    # Paths #
    #########

    # Indicates storage path for persistent data
    # STORAGE_PATH = os.getenv("STORAGE_PATH", default="/dataclay/storage/")

    ###########
    # Tracing #
    ###########

    # Destination path for traces
    # TRACES_DEST_PATH = os.getcwd()

    # extrae
    # tracing_enabled = False
    # extrae_starting_task_id = 0
    # pyclay_extrae_wrapper_lib = ""

    # TODO: This is a dangerous default, used in Docker but... useless everywhere else.
    # deploy_path = os.getenv("DEPLOY_PATH", "/dataclay/deploy")
    # deploy_path = deploy_path
    # deploy_path_source = os.getenv("DEPLOY_PATH_SRC", os.path.join(deploy_path, "source"))

    def load_backend_properties(self):
        self.THREAD_POOL_WORKERS = os.getenv("THREAD_POOL_WORKERS", default=None)

        self.DC_BACKEND_ID = None
        self.DC_BACKEND_NAME = os.getenv("DC_BACKEND_NAME")

        self.SERVER_LISTEN_ADDR = "0.0.0.0"
        self.SERVER_LISTEN_PORT = int(os.getenv("DATASERVICE_PYTHON_PORT_TCP", "6867"))

        self.ETCD_HOST = os.environ["ETCD_HOST"]
        self.ETCD_PORT = int(os.getenv("ETCD_PORT", "2379"))

    # TODO: Rename to client_proeprties?
    def load_client_properties(self):
        self.METADATA_SERVICE_HOST = os.environ["METADATA_SERVICE_HOST"]
        self.METADATA_SERVICE_PORT = int(os.getenv("METADATA_SERVICE_PORT", "16587"))

        self.DC_USERNAME = os.environ["DC_USERNAME"]
        self.DC_PASSWORD = os.environ["DC_PASSWORD"]
        self.DEFAULT_DATASET = os.environ["DEFAULT_DATASET"]
        self.LOCAL_BACKEND = os.getenv("LOCAL_BACKEND")

    def load_metadata_properties(self):
        self.THREAD_POOL_WORKERS = os.getenv("THREAD_POOL_WORKERS", default=None)

        self.SERVER_LISTEN_ADDR = "0.0.0.0"
        self.SERVER_LISTEN_PORT = int(os.getenv("METADATA_SERVICE_PORT_TCP", "16587"))

        self.ETCD_HOST = os.environ["ETCD_HOST"]
        self.ETCD_PORT = int(os.getenv("ETCD_PORT", "2379"))

        self.METADATA_SERVICE_HOST = os.getenv(
            "METADATA_SERVICE_HOST", socket.gethostbyname(socket.gethostname())
        )
        self.METADATA_SERVICE_PORT = int(os.getenv("METADATA_SERVICE_PORT", "16587"))


settings = Settings()
