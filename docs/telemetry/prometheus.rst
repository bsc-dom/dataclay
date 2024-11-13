Prometheus Example
==================

Deploy dataclay with Prometheus and Pushgateway:

.. note::
    This example is available in `GitHub <https://github.com/bsc-dom/dataclay/tree/main/examples/telemetry/prometheus>`_.

.. code-block:: bash

    docker compose up -d

The ``metadata-service`` and ``backends`` will post their metrics to the ``8000`` port.
Prometheus is configured to scrape this port to pull the metrics.

The ``client.py`` can also push metrics using the ``pushgateway``:

.. code-block:: bash

    export DATACLAY_METRICS=true
    export DATACLAY_METRICS_EXPORTER=pushgateway
    export DATACLAY_METRICS_HOST=localhost  # the default
    export DATACLAY_METRICS_PORT=9091
    python3 client.py

Go to ``localhost:9090/graph`` to explore the metrics with Prometheus.

.. note::
    When using ``pushgateway``, a new Python thread will run to push the metrics every 10 seconds.