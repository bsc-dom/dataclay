import os
import threading
import time

from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    push_to_gateway,
    start_http_server,
)
from prometheus_client.registry import REGISTRY


def pushgateway_thread(host, port, registry):
    while True:
        try:
            push_to_gateway(f"{host}:{port}", job="dataclay", registry=registry)
        except Exception as e:
            print(f"Error pushing to gateway: {e}")
        time.sleep(10)


def set_metrics(host, port, exporter):
    if exporter == "http":
        start_http_server(port)
    elif exporter == "pushgateway":
        thread = threading.Thread(target=pushgateway_thread, args=(host, port, registry))
        thread.start()


# TODO: Check if registry can be set aftwerwards by calling registry.register
registry = REGISTRY
exporter = os.getenv("DATACLAY_METRICS_EXPORTER", "http").lower()
if exporter == "pushgateway":
    registry = CollectorRegistry()

# Gauges
dataclay_inmemory_objects = Gauge(
    "dataclay_inmemory_objects", "Number of objects in memory", registry=registry
)
dataclay_loaded_objects = Gauge(
    "dataclay_loaded_objects", "Number of loaded objects in memory", registry=registry
)
dataclay_stored_objects = Gauge(
    "dataclay_stored_objects", "Number of stored objects", registry=registry
)


# Counters
dataclay_inmemory_misses_total = Counter(
    "dataclay_inmemory_misses_total", "Number of inmemory misses", registry=registry
)

dataclay_inmemory_hits_total = Counter(
    "dataclay_inmemory_hits_total", "Number of inmemory hits", registry=registry
)
