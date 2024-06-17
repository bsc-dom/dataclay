"""Configuration settings for dataClay (Client and Services).

The following classes contain all the configuration that are used by the different dataClay
services as well as by the :class:`~dataclay.client.api.Client`.

All the configuration can be set through environment variables. This is true for dataClay
deployment (i.e. services, so Backend, Metadata and Proxy) as well as for the client application.
"""

from __future__ import annotations

import contextvars
import logging
import socket
import uuid
from typing import TYPE_CHECKING, Annotated, Literal, Optional, Union

from pydantic import BaseSettings, Field, SecretStr, constr

if TYPE_CHECKING:
    from dataclay.runtime import BackendRuntime, ClientRuntime


class BackendSettings(BaseSettings):
    class Config:
        env_prefix = "dataclay_backend_"
        env_file = ".env"
        secrets_dir = "/run/secrets"

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: Optional[str] = None
    #: Hostname or IP address for this backend. This should be reachable by other dataClay services.
    #: By default, the hostname of the machine is used. Change if you are using an external reverse
    #: proxy or need to accommodate some NAT environment where manual port forwarding has been configured.
    host: str = socket.gethostbyname(socket.gethostname())
    #: Port for the backend service. Defaults to 6867.
    port: int = 6867
    #: Address to listen on. Defaults to 0.0.0.0 (any network).
    listen_address: str = "0.0.0.0"
    #: Enable healthcheck endpoint. Defaults to True.
    enable_healthcheck: bool = True


class MetadataSettings(BaseSettings):
    class Config:
        env_prefix = "dataclay_metadata_"
        env_file = ".env"
        secrets_dir = "/run/secrets"

    host: str = socket.gethostbyname(socket.gethostname())
    #: Port for the metadata service. Defaults to 16587.
    port: int = 16587
    #: Address to listen on. Defaults to 0.0.0.0 (any network).
    listen_address: str = "0.0.0.0"
    #: Enable healthcheck endpoint. Defaults to True.
    enable_healthcheck: bool = True


class ProxySettings(BaseSettings):
    class Config:
        env_prefix = "dataclay_proxy_"
        env_file = ".env"
        secrets_dir = "/run/secrets"

    port: int = 8676
    #: Address to listen on. Defaults to 0.0.0.0 (any network).
    listen_address: str = "0.0.0.0"
    #: Address of the metadata service.
    mds_host: str
    #: Port of the metadata service. Defaults to 16587.
    mds_port: int = 16587
    #: Python module to use for the proxy configuration. Defaults to "proxy_config".
    config_module: str = (
        "proxy_config"  # Could use ImportString, but ATM default values are not imported
    )


class ClientSettings(BaseSettings):
    class Config:
        env_prefix = "dc_"
        env_file = ".env"
        secrets_dir = "/run/secrets"

    password: str = "admin"
    #: Username to use for the client. Defaults to "admin".
    username: str = "admin"
    #: Dataset to use for the client. Defaults to "admin".
    dataset: str = "admin"
    #: Specifying this option will result in most client operations to be performed against this
    #: _local_ backend instead of being performed to a random backend.
    local_backend: Optional[str] = None
    dataclay_host: str = Field(default="localhost", alias="dc_host")
    dataclay_port: int = Field(default=16587, alias="dc_port")

    proxy_enabled: bool = False
    #: Hostname or IP address for the proxy service. Defaults to 127.0.0.1 (but proxy won't be used unless
    #: :attr:`proxy_enabled` is set to True).
    proxy_host: str = "127.0.0.1"
    #: Port for the proxy service. Defaults to 8676.
    proxy_port: int = 8676


class Settings(BaseSettings):
    class Config:
        env_prefix = "dataclay_"
        env_file = ".env"
        secrets_dir = "/run/secrets"

    # Other
    dataclay_id: Optional[uuid.UUID] = Field(default=None, alias="dataclay_id")
    storage_path: str = "/data/storage/"
    loglevel: constr(strip_whitespace=True, to_upper=True) = "INFO"
    ephemeral: bool = False

    # Threads
    #: Multiplier for I/O-bound tasks
    io_bound_multiplier: int = 2
    # TODO: Rename it with proxy...
    thread_pool_max_workers: Optional[int] = None
    healthcheck_max_workers: Optional[int] = None

    # Timeouts
    grpc_check_alive_timeout: int = 60
    unload_timeout: int = 5
    timeout_channel_ready: int = 5
    backend_clients_check_interval: int = 10
    shutdown_grace_period: int = 5

    # SSL
    ssl_client_trusted_certificates: str = ""
    ssl_client_certificate: str = ""
    ssl_client_key: str = ""
    ssl_target_authority: str = "proxy"
    ssl_target_ee_alias: str = "6867"

    # root account
    password: str = Field(default="admin")
    username: str = Field(default="admin")
    dataset: str = Field(default="admin")

    # Memory
    memory_threshold_high: float = 0.75
    memory_threshold_low: float = 0.50
    memory_check_interval: int = 10

    # Tracing
    service_name: Optional[str] = None
    tracing: bool = False
    tracing_exporter: Literal["otlp", "console", "none"] = "otlp"
    tracing_host: str = "localhost"
    tracing_port: int = 4317

    # Metrics
    metrics: bool = False
    metrics_exporter: Literal["http", "pushgateway", "none"] = "http"
    metrics_host: str = "localhost"
    metrics_port: int = 8000  # 9091 for pushgateway
    metrics_push_interval: int = 10

    # Services
    backend: Optional[BackendSettings] = None
    metadata: Optional[MetadataSettings] = None
    proxy: Optional[ProxySettings] = None
    client: Optional[ClientSettings] = None

    # key/value database
    kv_host: Optional[str] = None
    kv_port: int = 6379

    # TODO: Chech that kv_host is not None when calling from backend or metadata.

    # Destination path for traces
    # TRACES_DEST_PATH = os.getcwd()

    # Extrae
    # tracing_enabled = False
    # extrae_starting_task_id = 0
    # pyclay_extrae_wrapper_lib = ""


settings = Settings()


# Use for context-local data (current session, etc.)
session_var = contextvars.ContextVar("session")

current_runtime: Union[ClientRuntime, BackendRuntime, None] = None

exec_constraints_var = contextvars.ContextVar(
    "constraints", default={"max_threads": None, "max_memory": "1GB"}
)


def get_runtime() -> Union[ClientRuntime, BackendRuntime, None]:
    return current_runtime


def set_runtime(new_runtime: Union[ClientRuntime, BackendRuntime]):
    global current_runtime
    current_runtime = new_runtime


def logger_config(**kwargs):
    logging.basicConfig(**kwargs)


logger_config(level=settings.loglevel)
