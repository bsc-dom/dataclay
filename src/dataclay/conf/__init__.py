import logging
import socket
import uuid
from datetime import datetime
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr, constr
from pydantic_settings import BaseSettings, SettingsConfigDict


class BackendSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="dataclay_backend_", env_file=".env", secrets_dir="/run/secrets"
    )
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str | None = None
    host: str = socket.gethostbyname(socket.gethostname())
    port: int = 6867
    listen_address: str = "0.0.0.0"


class MetadataSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="dataclay_metadata_", env_file=".env", secrets_dir="/run/secrets"
    )
    host: str = socket.gethostbyname(socket.gethostname())
    port: int = 16587
    listen_address: str = "0.0.0.0"


class ClientSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="dc_", env_file=".env", secrets_dir="/run/secrets")
    password: SecretStr
    username: str
    dataset: str
    local_backend: str | None = None
    dataclay_host: str = Field(
        alias=AliasChoices("dc_host", "dataclay_metadata_host", "dataclay_host")
    )
    dataclay_port: int = Field(
        default=16587, alias=AliasChoices("dc_port", "dataclay_metadata_port", "dataclay_port")
    )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="dataclay_", env_file=".env", secrets_dir="/run/secrets"
    )

    # Other
    grpc_check_alive_timeout: int = 60
    ssl_client_trusted_certificates: str = ""
    ssl_client_certificate: str = ""
    ssl_client_key: str = ""
    ssl_target_authority: str = "proxy"
    ssl_target_ee_alias: str = "6867"
    unload_timeout: int = 5
    timeout_channel_ready: int = 5
    date_format: str = "%Y-%m-%dT%H:%M:%S"
    check_session: bool = False
    memmgmt_pressure_fraction: float = 0.75
    memmgmt_ease_fraction: float = 0.50
    memmgmt_check_time_interval: int = 5000
    nocheck_session_expiration: datetime = datetime.strptime("2120-09-10T20:00:04", date_format)

    # root account
    root_password: SecretStr = Field(default="admin", alias="dataclay_password")
    root_username: str = Field(default="admin", alias="dataclay_username")
    root_dataset: str = Field(default="admin", alias="dataclay_dataset")

    dataclay_id: uuid.UUID | None = Field(default=None, alias="dataclay_id")

    storage_path: str = "/dataclay/storage/"
    thread_pool_workers: int | None = None
    loglevel: constr(to_upper=True) = "WARNING"

    # tracing
    service_name: str | None = None
    tracing: bool = False
    tracing_exporter: Literal["otlp", "jaeger", "zipkin", "none"] = "otlp"
    tracing_host: str = "localhost"
    tracing_port: int = 4317

    # metrics
    metrics: bool = False
    metrics_exporter: Literal["http", "prometheus", "none"] = "http"
    metrics_host: str = "localhost"
    metrics_port: int = 8000  # 9091 for pushgateway
    metrics_push_interval: int = 10

    # services
    backend: BackendSettings | None = None
    metadata: MetadataSettings | None = None
    client: ClientSettings | None = None

    # key/value
    kv_host: str | None = None
    kv_port: int = 6379

    # TODO: Chech that kv_host is not None when calling from backend or metadata.

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

    # Grace period to wait for and object to relase the lock before forcing to unload.


settings = Settings()


logging.basicConfig(level=settings.loglevel)
