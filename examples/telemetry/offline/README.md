# Offline Telemetry Example

This example demonstrates how to export opentelemetry traces to a JSON file and then
visualize in Grafana.

To activate traces in dataClay, you need to set the following environment variables:

- `DATACLAY_TRACING`: Set to `true` to enable tracing.
- `DATACLAY_TRACING_EXPORTER`: Set to `otlp` to export traces to the OpenTelemetry Collector, or `console` to print traces to the console (default is `otlp`).
- `DATACLAY_TRACING_HOST`: The host of the OpenTelemetry Collector (default is `localhost`).
- `DATACLAY_TRACING_PORT`: The port of the OpenTelemetry Collector (default is 4317).
- `DATACLAY_SERVICE_NAME`: The service name.

## Generating Traces and Exporting to JSON file

Go into the `json-exporter` folder:

```bash
cd json-exporter
```

Start the dataClay and OpenTelemetry Collector services:

```bash
docker compose up
```

Run the dataClay client to generate some traces:

```bash
python3 client.py
```

The traces are exported to the `traces` folder. You can view the traces in the JSON file.

## Visualizing the Traces in Grafana

Go into the `json-post-mortem` folder:

```bash
cd json-post-mortem
```

Start the OpenTelemetry Collector, Tempo, and Grafana services:

```bash
docker compose up
```

Open the Grafana UI in your browser at <http://localhost:3000>. The default username and password are both `admin`.

Navigate to the `Explore` section and select the `Tempo` data source. You can query the traces using the `Trace ID` field.

You could also run manually the OpenTelemetry Collector with the following command:

```bash
docker run \
-v ./config/otel-collector.yaml:/etc/otel-collector.yaml \
otel/opentelemetry-collector-contrib \
"--config=/etc/otel-collector.yaml"
```

## Troubleshooting

If you get a `permission denied` error for the `/traces` folder, then you need to give the permission to the `traces` folder.

```bash
sudo chmod -R 777 traces
```

<http://localhost:3000>
