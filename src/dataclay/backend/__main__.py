"""Entry point for standalone dataClay Backend server."""

import asyncio
import logging

from dataclay.backend import servicer
from dataclay.config import BackendSettings, settings

logger = logging.getLogger(__name__)

settings.backend = BackendSettings()
logger.info("Backend settings: %s", settings.backend)

# Start tracing and metrics
if settings.service_name is None:
    settings.service_name = "backend"

if settings.tracing:
    # pylint: disable=import-outside-toplevel
    import dataclay.utils.telemetry

    dataclay.utils.telemetry.set_tracing(
        settings.service_name,
        settings.tracing_host,
        settings.tracing_port,
        settings.tracing_exporter,
    )

if settings.metrics:
    # pylint: disable=import-outside-toplevel
    import dataclay.utils.metrics

    dataclay.utils.metrics.set_metrics(
        settings.metrics_host,
        settings.metrics_port,
        settings.metrics_exporter,
    )

asyncio.run(servicer.serve())
