# Real-time Telemetry Example

This example demonstrates how to run a real-time telemetry pipeline with dataClay and OpenTelemetry, and visualize the traces in Grafana.

To activate traces in dataClay, you need to set the following environment variables:

- `DATACLAY_TRACING`: Set to `true` to enable tracing.
- `DATACLAY_TRACING_EXPORTER`: Set to `otlp` to export traces to the OpenTelemetry Collector, or `console` to print traces to the console (default is `otlp`).
- `DATACLAY_TRACING_HOST`: The host of the OpenTelemetry Collector (default is `localhost`).
- `DATACLAY_TRACING_PORT`: The port of the OpenTelemetry Collector (default is 4317).
- `DATACLAY_SERVICE_NAME`: The service name.

## Running the Real-time Telemetry Pipeline

Go into the `real-time` folder:

```bash
cd real-time
```

Start the dataClay and OpenTelemetry Collector services:

```bash
docker compose up
```

Run the dataClay client to generate some traces:

```bash
python3 client.py
```

The traces are exported to the OpenTelemetry Collector. You can view the traces in the Grafana UI at <http://localhost:3000>. The default username and password are both `admin`.

Navigate to the `Explore` section and select the `Tempo` data source. You can query the traces using the `Trace ID` field. Also, you can see the services and their interactions in the `Service Graph` section.
