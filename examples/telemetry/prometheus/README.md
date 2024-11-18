# Prometheus

## Metrics

| Metric                       | Description               | Service          |
|------------------------------|---------------------------|------------------|
| `dataclay_inmemory_objects`  | Number of objects in memory | backend, client |
| `dataclay_loaded_objects`    | Number of loaded objects    | backend          |
| `dataclay_stored_objects`    | Number of stored objects    | backend          |
| `dataclay_inmemory_misses_total` | Number of inmemory misses | backend, client |
| `dataclay_inmemory_hits_total`   | Number of inmemory hits   | backend, client |

## Deploy

Run dataClay with Prometheus:

```bash
docker compose up -d
```

The `metadata-service` and `backends` will post their metrics to `8000` port.
Prometheus is configured to scrape this port to pull the metrics.

Access Prometheus at [http://localhost:9090](http://localhost:9090). You can query the metrics defined above.

<!-- TODO: Check if can obtain metrics from client running in localhost -->