
Real-time Telemetry Example
===========================

This example demonstrates running a real-time telemetry pipeline.

1. **Activate tracing** by setting environment variables as described in the `telemetry configuration <https://dataclay.bsc.es/docs/telemetry/configuration>`_.
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
