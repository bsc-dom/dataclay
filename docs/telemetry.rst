Telemetry
=========

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

Offline Telemetry Example
-------------------------

This example demonstrates exporting OpenTelemetry traces to a JSON file for post-mortem analysis in Grafana.

1. **Activate tracing** by setting environment variables as described above.
2. **Generate traces**:

   - Navigate to the `json-exporter` folder in the `offline telemetry example JSON exporter <https://github.com/bsc-dom/dataclay/tree/telemetry-doc/examples/telemetry/offline/json-exporter>`_.
   - Start dataClay and OpenTelemetry Collector services:
     
     .. code-block:: bash

        docker compose up
     
   - Run the dataClay client:
     
     .. code-block:: bash

        python3 client.py
     
   - Traces are exported to the `traces` folder. You can visualize the JSON traces in Grafana.

3. **Visualize in Grafana**:

   - Navigate to the `json-post-mortem` folder in the `offline telemetry example post-mortem <https://github.com/bsc-dom/dataclay/tree/telemetry-doc/examples/telemetry/offline/json-post-mortem>`_.
   - Start the OpenTelemetry Collector, Tempo, and Grafana services:
     
     .. code-block:: bash

        docker compose up
     
   - Open Grafana at <http://localhost:3000> (default username/password: `admin`/`admin`).
   - In the `Explore` section, select `Tempo` as the data source and use the `Trace ID` field to query traces.

4. **Alternative Trace Export**:

   - Run the OpenTelemetry Collector manually:
     
     .. code-block:: bash

        docker run \
        -v ./config/otel-collector.yaml:/etc/otel-collector.yaml \
        otel/opentelemetry-collector-contrib \
        "--config=/etc/otel-collector.yaml"

5. **Copy Traces from MareNostrum 5**:

   - To analyze traces from MareNostrum 5, copy them locally:
     
     .. code-block:: bash

        scp transfer1.bsc.es:~/.dataclay/otel-traces.json ./traces/otel-traces.json

6. **Troubleshooting**:

   - If permission issues arise for the `/traces` folder, adjust permissions:
     
     .. code-block:: bash

        sudo chmod -R 777 traces

Real-time Telemetry Example
---------------------------

This example demonstrates running a real-time telemetry pipeline.

1. **Activate tracing** by setting environment variables as described above.
2. **Start services and generate traces**:

   - Go to the `real-time telemetry example folder <https://github.com/bsc-dom/dataclay/tree/telemetry-doc/examples/telemetry/real-time>`_.
   - Start dataClay and OpenTelemetry Collector services:
     
     .. code-block:: bash

        docker compose up
     
   - Run the dataClay client:
     
     .. code-block:: bash

        python3 client.py
     
   - The traces are streamed in real-time to the OpenTelemetry Collector.

3. **Visualize in Grafana**:

   - Access Grafana at <http://localhost:3000> (default username/password: `admin`/`admin`).
   - In the `Explore` section, select `Tempo` as the data source to query traces. You can also view interactions in the `Service Graph` section.
