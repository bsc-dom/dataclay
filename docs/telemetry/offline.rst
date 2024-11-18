
Offline Telemetry Example
=========================

This example demonstrates exporting OpenTelemetry traces to a JSON file for post-mortem analysis in Grafana.

1. **Activate tracing** by setting environment variables as described in the `telemetry configuration <https://dataclay.bsc.es/docs/telemetry/configuration>`_.
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
