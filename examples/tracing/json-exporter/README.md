
# JSON Exporter

This example demonstrates how to export opentelemetry traces to a JSON file. The JSON file is created in the `traces` folder.

To activate traces in dataClay, you need to set the following environment variables:

- `DATACLAY_TRACING`: Set to `true` to enable tracing.
- `DATACLAY_TRACING_EXPORTER`: Set to `otlp` to export traces to the OpenTelemetry Collector, or `console` to print traces to the console (default is `otlp`).
- `DATACLAY_TRACING_HOST`: The host of the OpenTelemetry Collector (default is `localhost`).
- `DATACLAY_TRACING_PORT`: The port of the OpenTelemetry Collector (default is 4317).
- `DATACLAY_SERVICE_NAME`: The service name.

## Running the Example

Start the dataClay services:

```bash
docker compose up
```

Run the example:

```bash
python3 client.py
```

The traces are exported to the `traces` folder. You can view the traces in the JSON file.

## Troubleshooting

If you get this error `open /traces/otel-traces.json: permission denied`, then you need to give the permission to the `traces` folder.

```bash
sudo chmod -R 777 traces
```
