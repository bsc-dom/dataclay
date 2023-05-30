from prometheus_client import Counter, Gauge, start_http_server


def set_prometheus(port=8000):
    start_http_server(port)


# Gauges
dataclay_inmemory_objects = Gauge("dataclay_inmemory_objects", "Number of objects in memory")
dataclay_loaded_objects = Gauge("dataclay_loaded_objects", "Number of loaded objects in memory")
dataclay_stored_objects = Gauge("dataclay_stored_objects", "Number of stored objects")


# Counters
dataclay_inmemory_misses_total = Counter(
    "dataclay_inmemory_misses_total", "Number of inmemory misses"
)

dataclay_inmemory_hits_total = Counter("dataclay_inmemory_hits_total", "Number of inmemory hits")
