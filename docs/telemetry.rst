Telemetry
=========

dataClay is instrumented with `OpenTelemetry <https://opentelemetry.io/>`_ to allow observability of
distributed traces, metrics and logs.





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
