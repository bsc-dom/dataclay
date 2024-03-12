"""Entry point for standalone dataClay Metadata server."""

import asyncio
import logging

from dataclay.config import MetadataSettings, settings
from dataclay.metadata import servicer

logger = logging.getLogger(__name__)

settings.metadata = MetadataSettings()
logger.info("MetadataService settings: %s", settings.metadata)

# Start tracing and metrics
if settings.service_name is None:
    settings.service_name = "metadata"

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
