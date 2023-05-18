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

    docker compose up

This will deploy a dataClay instance with a single backend. To deploy three backends you can
add two more backend services to the previous ``docker-compose``:

.. code-block:: yaml

    backend_2:
      image: "ghcr.io/bsc-dom/dataclay:edge"
      depends_on:
        - redis
      ports:
        - 6868:6868
      environment:
        - DATACLAY_KV_HOST=redis
        - DATACLAY_KV_PORT=6379
        - DATACLAY_BACKEND_ID
        - DATACLAY_BACKEND_NAME
        - DATACLAY_BACKEND_PORT=6868
        - DATACLAY_LOGLEVEL=DEBUG
      command: python -m dataclay.backend
      volumes:
        - ./model:/workdir/model:ro

    backend_3:
      image: "ghcr.io/bsc-dom/dataclay:edge"
      depends_on:
        - redis
      ports:
        - 6869:6869
      environment:
        - DATACLAY_KV_HOST=redis
        - DATACLAY_KV_PORT=6379
        - DATACLAY_BACKEND_ID
        - DATACLAY_BACKEND_NAME
        - DATACLAY_BACKEND_PORT=6869
        - DATACLAY_LOGLEVEL=DEBUG
      command: python -m dataclay.backend
      volumes:
        - ./model:/workdir/model:ro

Notice that we have changed the ``DATACLAY_BACKEND_PORT`` environment variable to avoid port conflicts.

Account Managment
-----------------

First export the following environment variables with the corresponding value::

    export DC_HOST=127.0.0.1

To create a new account::

    dataclay new_account john s3cret

To create a new dataset::

    dataclay new_dataset john s3cret mydataset
