import logging
import os
import socket
import uuid
from datetime import datetime

import dataclay.utils.telemetry


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

    # ETCD_PATH ¿?

    #############
    # Telemetry #
    #############

    DATACLAY_TRACING = os.getenv("DATACLAY_TRACING", default="false").lower() == "true"
    _tracing_loaded = False

    DATACLAY_LOGLEVEL = os.getenv("DATACLAY_LOGLEVEL", default="WARNING").upper()
    logging.basicConfig(level=DATACLAY_LOGLEVEL)

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

        self.DATACLAY_BACKEND_ID = os.getenv("DATACLAY_BACKEND_ID", uuid.uuid4())
        self.DATACLAY_BACKEND_NAME = os.getenv("DATACLAY_BACKEND_NAME")

        self.DATACLAY_BACKEND_LISTEN_ADDRESS = "0.0.0.0"
        self.DATACLAY_BACKEND_PORT = int(os.getenv("DATACLAY_BACKEND_PORT", "6867"))
        self.DATACLAY_BACKEND_HOSTNAME = os.getenv(
            "DATACLAY_BACKEND_HOSTNAME", socket.gethostbyname(socket.gethostname())
        )

        # self.ETCD_HOSTNAME = os.environ["ETCD_HOSTNAME"]
        # self.ETCD_PORT = int(os.getenv("ETCD_PORT", "2379"))

        self.DATACLAY_KV_HOST = os.environ["DATACLAY_KV_HOST"]
        self.DATACLAY_KV_PORT = int(os.getenv("DATACLAY_KV_PORT", "6379"))

        self.STORAGE_PATH = os.getenv("STORAGE_PATH", default="/dataclay/storage/")

        self.DATACLAY_SERVICE_NAME = os.getenv("DATACLAY_SERVICE_NAME", "backend")
        self.load_tracing_properties()

    # TODO: Rename to client_proeprties?
    def load_client_properties(
        self, host=None, port=None, username=None, password=None, dataset=None, local_backend=None
    ):
        self.DATACLAY_METADATA_HOSTNAME = (
            host or os.getenv("DATACLAY_METADATA_HOSTNAME") or os.environ["DC_HOST"]
        )
        self.DATACLAY_METADATA_PORT = int(
            port or os.getenv("DATACLAY_METADATA_PORT") or os.getenv("DC_PORT", "16587")
        )

        self.DC_USERNAME = username or os.environ["DC_USERNAME"]
        self.DC_PASSWORD = password or os.environ["DC_PASSWORD"]
        self.DC_DATASET = dataset or os.environ["DC_DATASET"]
        self.LOCAL_BACKEND = local_backend or os.getenv("LOCAL_BACKEND")

    def load_metadata_properties(self):
        self.THREAD_POOL_WORKERS = os.getenv("THREAD_POOL_WORKERS", default=None)

        self.DATACLAY_METADATA_LISTEN_ADDRESS = "0.0.0.0"
        self.DATACLAY_METADATA_PORT = int(os.getenv("DATACLAY_METADATA_PORT", "16587"))
        self.DATACLAY_METADATA_HOSTNAME = os.getenv(
            "DATACLAY_METADATA_HOSTNAME", socket.gethostbyname(socket.gethostname())
        )

        # self.ETCD_HOSTNAME = os.environ["ETCD_HOSTNAME"]
        # self.ETCD_PORT = int(os.getenv("ETCD_PORT", "2379"))

        self.DATACLAY_KV_HOST = os.environ["DATACLAY_KV_HOST"]
        self.DATACLAY_KV_PORT = int(os.getenv("DATACLAY_KV_PORT", "6379"))

        self.DATACLAY_ID = os.getenv("DATACLAY_ID", uuid.uuid4())
        self.DATACLAY_PASSWORD = os.environ["DATACLAY_PASSWORD"]
        self.DATACLAY_USERNAME = os.getenv("DATACLAY_USERNAME", "dataclay")
        self.DATACLAY_DATASET = os.getenv("DATACLAY_DATASET", self.DATACLAY_USERNAME)

        self.DATACLAY_SERVICE_NAME = os.getenv("DATACLAY_SERVICE_NAME", "metadata")
        self.load_tracing_properties()

    def load_tracing_properties(self, service_name=None):
        if self._tracing_loaded:
            logger.warning(
                "Attempting to reload tracing properties while already instrumented. Ignoring!"
            )
            return

        if service_name is None:
            service_name = self.DATACLAY_SERVICE_NAME

        if self.DATACLAY_TRACING:
            self.DATACLAY_TRACING_EXPORTER = os.getenv("DATACLAY_TRACING_EXPORTER", "otlp")
            self.DATACLAY_TRACING_HOST = os.getenv("DATACLAY_TRACING_HOST", "localhost")
            self.DATACLAY_TRACING_PORT = int(os.getenv("DATACLAY_TRACING_PORT", "4317"))
            dataclay.utils.telemetry.set_tracer_provider(
                service_name, self.DATACLAY_TRACING_HOST, self.DATACLAY_TRACING_PORT
            )

        self._tracing_loaded = True


settings = Settings()
