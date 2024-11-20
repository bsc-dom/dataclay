Prometheus
==========


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


Deploy dataClay with Prometheus
-------------------------------

Run dataClay with Prometheus:

.. note::
    This example is available in `GitHub <https://github.com/bsc-dom/dataclay/tree/main/examples/telemetry/prometheus>`__.

.. code-block:: bash

    docker compose up -d

The ``metadata-service`` and ``backends`` will post their metrics to the ``8000`` port.
Prometheus is configured to scrape this port to pull the metrics.

Access Prometheus at `http://localhost:9090 <http://localhost:9090>`_. You can query the metrics defined above.


Deploy dataClay with Prometheus Pushgateway
-------------------------------------------

Run dataClay with Prometheus Pushgateway:

.. note::
    This example is available in `GitHub <https://github.com/bsc-dom/dataclay/tree/main/examples/telemetry/prometheus-pushgateway>`__.

.. code-block:: bash
    
    docker compose up -d


The ``metadata-service`` and ``backends`` will push their metrics to the ``pushgateway`` at the ``9091`` port.

The ``client.py`` can also push metrics using the ``pushgateway``:

.. code-block:: bash

    export DATACLAY_METRICS=true
    export DATACLAY_METRICS_EXPORTER=pushgateway
    export DATACLAY_METRICS_HOST=localhost  # the default
    export DATACLAY_METRICS_PORT=9091
    python3 client.py


Access the Pushgateway at `http://localhost:9091 <http://localhost:9091>`_ and Prometheus at `http://localhost:9090 <http://localhost:9090>`_.

.. note::
    When using ``pushgateway``, a new Python thread will run to push the metrics every 10 seconds (default).