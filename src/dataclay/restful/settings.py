import enum
from pathlib import Path
from tempfile import gettempdir
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

TEMP_DIR = Path(gettempdir())


class LogLevel(str, enum.Enum):  # noqa: WPS600
    """Possible log levels."""

    NOTSET = "NOTSET"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"


class Settings(BaseSettings):
    """
    Application settings.

    These parameters can be configured
    with environment variables.
    """

    host: str = "127.0.0.1"
    port: int = 8000
    # quantity of workers for uvicorn
    workers_count: int = 1
    # Enable uvicorn reloading
    reload: bool = False

    # Current environment
    environment: str = "dev"

    log_level: LogLevel = LogLevel.INFO

    # Grpc endpoint for opentelemetry.
    # E.G. http://localhost:4317
    opentelemetry_endpoint: Optional[str] = None
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="DATACLAY_RESTFUL_",
        env_file_encoding="utf-8",
    )


settings = Settings()
