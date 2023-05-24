Deployment
==========

The easiest way to deploy dataClay is using the provided 
`docker image <https://github.com/bsc-dom/dataclay/pkgs/container/dataclay>`_. 
You can deploy a minimal dataClay instance with the following ``docker-compose``:

.. literalinclude:: /../examples/quickstart/docker-compose.yml
   :language: yaml

.. note::
    All dataClay classes must be saved in the ``model`` folder to allow access by the backends.
    In more complex deployments, the class models will be embedded in the docker image, installed
    with ``pip``, or deployed somehow.

To deploy the ``docker-compose`` just run::

    docker compose up -d

This will deploy a dataClay instance with a single backend. To deploy three backends you can
add two more backend services to the previous ``docker-compose``:

.. code-block:: yaml

    backend_2:
      image: "ghcr.io/bsc-dom/dataclay:edge"
      depends_on:
        - redis
      environment:
        - DATACLAY_KV_HOST=redis
      command: python -m dataclay.backend
      volumes:
        - ./model:/workdir/model:ro

    backend_3:
      image: "ghcr.io/bsc-dom/dataclay:edge"
      depends_on:
        - redis
      environment:
        - DATACLAY_KV_HOST=redis
      command: python -m dataclay.backend
      volumes:
        - ./model:/workdir/model:ro

        
.. list of all environment variables

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
     - /dataclay/storage/
   * - DATACLAY_LISTEN_ADDRESS
     - The listen address
     - metadata, backend
     - 0.0.0.0
   * - DATACLAY_LOGLEVEL
     - The log level
     - metadata, backend, client
     - warning
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


Account Managment
-----------------

First export the following environment variables with the corresponding value::

    export DC_HOST=127.0.0.1

To create a new account::

    dataclay new_account john s3cret

To create a new dataset::

    dataclay new_dataset john s3cret mydataset
