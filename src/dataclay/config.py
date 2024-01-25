import logging
import socket
import uuid
from typing import Annotated, Literal, Optional

from pydantic import AliasChoices, Field, StringConstraints
from pydantic_settings import BaseSettings, SettingsConfigDict


class BackendSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="dataclay_backend_", env_file=".env", secrets_dir="/run/secrets", extra="ignore"
    )
    id: Optional[uuid.UUID] = None
    name: Optional[str] = None
    host: str = socket.gethostbyname(socket.gethostname())
    port: int = 6867
    listen_address: str = "0.0.0.0"
    enable_healthcheck: bool = True


class MetadataSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="dataclay_metadata_", env_file=".env", secrets_dir="/run/secrets", extra="ignore"
    )
    host: str = socket.gethostbyname(socket.gethostname())
    port: int = 16587
    listen_address: str = "0.0.0.0"
    enable_healthcheck: bool = True


class ProxySettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="dataclay_proxy_", env_file=".env", secrets_dir="/run/secrets", extra="ignore"
    )
    port: int = 8676
    listen_address: str = "0.0.0.0"
    mds_host: str
    mds_port: int = 16587
    config_module: str = (
        "proxy_config"  # Could use ImportString, but ATM default values are not imported
    )


class ClientSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="dc_", env_file=".env", secrets_dir="/run/secrets", extra="ignore"
    )
    password: str = "admin"
    username: str = "admin"
    dataset: str = "admin"
    local_backend: Optional[str] = None
    dataclay_host: str = Field(
        default="localhost",
        alias=AliasChoices("dc_host", "dataclay_metadata_host", "dataclay_host"),
    )
    dataclay_port: int = Field(
        default=16587, alias=AliasChoices("dc_port", "dataclay_metadata_port", "dataclay_port")
    )
    proxy_enabled: bool = False
    proxy_host: str = "127.0.0.1"
    proxy_port: int = 8676


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="dataclay_", env_file=".env", secrets_dir="/run/secrets", extra="ignore"
    )

    # Other
    dataclay_id: Optional[uuid.UUID] = Field(default=None, alias="dataclay_id")
    storage_path: str = "/data/storage/"
    check_session: bool = False
    thread_pool_max_workers: Optional[int] = None
    healthcheck_max_workers: Optional[int] = None
    loglevel: Annotated[str, StringConstraints(strip_whitespace=True, to_upper=True)] = "INFO"
    ephemeral: bool = False

    # Timeouts
    grpc_check_alive_timeout: int = 60
    unload_timeout: int = 5
    timeout_channel_ready: int = 5
    backend_clients_check_interval: int = 10

    # SSL
    ssl_client_trusted_certificates: str = ""
    ssl_client_certificate: str = ""
    ssl_client_key: str = ""
    ssl_target_authority: str = "proxy"
    ssl_target_ee_alias: str = "6867"

    # Memory
    memory_threshold_high: float = 0.75
    memory_threshold_low: float = 0.50
    memory_check_interval: int = 10

    # Root account
    root_password: str = Field(default="admin", alias="dataclay_password")
    root_username: str = Field(default="admin", alias="dataclay_username")
    root_dataset: str = Field(default="admin", alias="dataclay_dataset")

    # Tracing
    service_name: Optional[str] = None
    tracing: bool = False
    tracing_exporter: Literal["otlp", "jaeger", "zipkin", "none"] = "otlp"
    tracing_host: str = "localhost"
    tracing_port: int = 4317

    # Metrics
    metrics: bool = False
    metrics_exporter: Literal["http", "prometheus", "none"] = "http"
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


logging.basicConfig(level=settings.loglevel)
