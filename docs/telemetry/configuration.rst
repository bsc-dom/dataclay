Telemetry Configuration
=======================

dataClay is instrumented with `OpenTelemetry <https://opentelemetry.io/>`_ to allow observability of
distributed traces, metrics, and logs. You can configure tracing to export telemetry data either in real-time or for post-mortem analysis. Visualizations can be performed in Grafana.

Configuration
-------------

To activate tracing in dataClay, the following environment variables need to be set:

- **`DATACLAY_TRACING`**: Set to `true` to enable tracing.
- **`DATACLAY_TRACING_EXPORTER`**: Export traces to the OpenTelemetry Collector (`otlp`) or print traces to the console (`console`). The default is `otlp`.
- **`DATACLAY_TRACING_HOST`**: Host of the OpenTelemetry Collector (default: `localhost`).
- **`DATACLAY_TRACING_PORT`**: Port of the OpenTelemetry Collector (default: `4317`).
- **`DATACLAY_SERVICE_NAME`**: The service name, which identifies dataClay components in trace data.

Metrics
-------

.. list-table::
   :header-rows: 1

   * - Metric
     - Description
     - Service
   * - dataclay_inmemory_objects
     - Number of objects in memory
     - backend, client
   * - dataclay_loaded_objects
     - Number of loaded objects
     - backend
   * - dataclay_stored_objects
     - Number of stored objects
     - backend
   * - dataclay_inmemory_misses_total
     - Number of inmemory misses
     - backend, client
   * - dataclay_inmemory_hits_total
     - Number of inmemory hits
     - backend, client
