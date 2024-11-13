# Prometheus

Deploy dataclay with Prometheus and pushgateway:

```bash
docker compose up -d
```

The `metadata-service` and `backends` will post their metrics to `8000` port.
Prometheus is configured to scrape this port to pull the metrics.

The `client.py` can also push metris using the `pushgateway`:

```bash
export DATACLAY_METRICS=true
export DATACLAY_METRICS_EXPORTER=pushgateway
export DATACLAY_METRICS_HOST=localhost # the default
export DATACLAY_METRICS_PORT=9091
python3 client.py
```

Go to `localhost:9090/graph` to explore the metrics wiht `Prometheus`.

Note: When using `pushgateway` a new python thread will run to push the metrics every 10 seconds.
