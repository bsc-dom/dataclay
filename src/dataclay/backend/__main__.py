"""Entry point for standalone dataClay Backend server."""

import dataclay.utils.metrics
import dataclay.utils.telemetry
from dataclay.backend import servicer
from dataclay.config import BackendSettings, settings

settings.backend = BackendSettings()

# Start tracing and metrics
if settings.service_name is None:
    settings.service_name = "backend"

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
