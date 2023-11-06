Config environment variables
============================

This is a list of all environment variables that can be used to configure dataClay.

.. list-table::
   :widths: 40 40 15 15
   :header-rows: 1

   * - Environment Variable
     - Description
     - Service
     - Default Value
   * - DATACLAY_KV_HOST
     - The key-value store hostname
     - metadata, backend
     -
   * - DATACLAY_KV_PORT
     - The key-value store port
     - metadata, backend
     - 6379
   * - DATACLAY_ID
     - The dataclay instance ID
     - metadata
     - random
   * - DATACLAY_METADATA_HOST
     - The metadata hostname
     - metadata
     - socket hostname
   * - DATACLAY_METADATA_PORT
     - The metadata port
     - metadata
     - 16587
   * - DATACLAY_PASSWORD
     - The admin password
     - metadatas
     - admin
   * - DATACLAY_USERNAME
     - The admin username
     - metadata
     - admin
   * - DATACLAY_DATASET
     - The admin dataset
     - metadata
     - admin
   * - DATACLAY_BACKEND_ID
     - The backend ID
     - backend
     - random
   * - DATACLAY_BACKEND_NAME
     - The backend name
     - backend
     -
   * - DATACLAY_BACKEND_HOST
     - The backend hostname
     - backend
     - socket hostname
   * - DATACLAY_BACKEND_PORT
     - The backend port
     - backend
     - 6867
   * - DATACLAY_STORAGE_PATH
     - The backend storage path
     - backend
     - /data/storage/
   * - DATACLAY_LISTEN_ADDRESS
     - The listen address
     - metadata, backend
     - 0.0.0.0
   * - DATACLAY_LOGLEVEL
     - The log level
     - metadata, backend, client
     - warning
   * - DATACLAY_METRICS
     - Enable metrics
     - metadata, backend, client
     - false
   * - DATACLAY_TRACING
     - Enable tracing
     - metadata, backend, client
     - false
   * - DATACLAY_TRACING_EXPORTER
     - The tracing exporter (otlp, console)
     - metadata, backend, client
     - otlp
   * - DATACLAY_TRACING_HOST
     - The tracing host
     - metadata, backend, client
     - localhost
   * - DATACLAY_TRACING_PORT
     - The tracing port
     - metadata, backend, client
     - 4317
   * - DATACLAY_SERVICE_NAME
     - The service name
     - metadata, backend, client
     - metadata, backend, client
