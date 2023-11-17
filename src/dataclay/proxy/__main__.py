"""Entry point for the Proxy server."""

import logging

import dataclay.utils.metrics
import dataclay.utils.telemetry
from dataclay.proxy import servicer
from dataclay.config import ProxySettings, settings

logger = logging.getLogger(__name__)

settings.proxy = ProxySettings()
logger.info("Proxy settings: %s", settings.proxy)

# Start tracing and metrics
if settings.service_name is None:
    settings.service_name = "proxy"

if settings.tracing:
    dataclay.utils.telemetry.set_tracing(
        settings.service_name,
        settings.tracing_host,
        settings.tracing_port,
        settings.tracing_exporter,
    )

if settings.metrics:
    dataclay.utils.metrics.set_metrics(
        settings.metrics_host,
        settings.metrics_port,
        settings.metrics_exporter,
    )

servicer.serve()
