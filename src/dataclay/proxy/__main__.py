"""Entry point for the Proxy server."""

import importlib
import logging
import asyncio

from dataclay.config import ProxySettings, settings
from dataclay.metadata.api import MetadataAPI
from dataclay.proxy import servicer

logger = logging.getLogger(__name__)

settings.proxy = ProxySettings()
logger.info("Proxy settings: %s", settings.proxy)

# Start tracing and metrics
if settings.service_name is None:
    settings.service_name = "proxy"

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

md_api = MetadataAPI(settings.kv_host, settings.kv_port)

# Prepare defaults (empty lists)
interceptors = list()
middleware_backend = list()
middleware_metadata = list()

# Now some convoluted code to get the user-defined interceptors and middleware
# (if any, otherwise keep the defaults)
try:
    config_module = importlib.import_module(settings.proxy.config_module)
except ImportError:
    logger.info(
        "Could not import %s, proceeding with default proxy configuration",
        settings.proxy.config_module,
    )
else:
    # At this point, there *is* a config_module but it may or may not contain
    # any of the following configuration entries:
    logger.info("Using config module in %s", config_module.__file__)
    try:
        interceptors = config_module.interceptors
    except AttributeError:
        pass
    try:
        middleware_metadata = config_module.middleware_metadata
    except AttributeError:
        pass
    try:
        middleware_backend = config_module.middleware_backend
    except AttributeError:
        pass

asyncio.run(servicer.serve(md_api, interceptors, middleware_metadata, middleware_backend))
