# Prometheus Pushgateway

## Metrics

| Metric                       | Description               | Service          |
|------------------------------|---------------------------|------------------|
| `dataclay_inmemory_objects`  | Number of objects in memory | backend, client |
| `dataclay_loaded_objects`    | Number of loaded objects    | backend          |
| `dataclay_stored_objects`    | Number of stored objects    | backend          |
| `dataclay_inmemory_misses_total` | Number of inmemory misses | backend, client |
| `dataclay_inmemory_hits_total`   | Number of inmemory hits   | backend, client |

## Deploy

Run dataClay with Prometheus and Pushgateway:

```bash
docker compose up -d
```

The `metadata-service` and `backends` will push their metrics to the `pushgateway` at `9091` port.

The `client.py` can also push metris using the `pushgateway`:

```bash
export DATACLAY_METRICS=true
export DATACLAY_METRICS_EXPORTER=pushgateway
export DATACLAY_METRICS_HOST=localhost # the default
export DATACLAY_METRICS_PORT=9091
python3 client.py
```

Access the Pushgateway at [http://localhost:9091](http://localhost:9091) and Prometheus at [http://localhost:9090](http://localhost:9090).

Note: When using `pushgateway`, a new Python thread will run to push the metrics every 10 seconds (default).
