Deployment
==========

The easiest way to deploy dataClay is using the provided docker image. 
You can deploy a minimal dataClay instance with:

.. code-block:: yaml

    version: '3.9'
    services:

    redis:
        image: redis:latest
        ports:
        - 6379:6379

    metadata-service:
        image: "ghcr.io/bsc-dom/dataclay:edge"
        depends_on:
        - redis
        ports:
        - 16587:16587
        environment:
        - DATACLAY_KV_HOST=redis
        - DATACLAY_KV_PORT=6379
        - DATACLAY_ID
        - DATACLAY_PASSWORD=s3cret
        - DATACLAY_USERNAME=testuser
        - DATACLAY_METADATA_PORT=16587
        command: python -m dataclay.metadata

    backend:
        image: "ghcr.io/bsc-dom/dataclay:edge"
        depends_on:
        - redis
        ports:
        - 6867:6867
        environment:
        - DATACLAY_KV_HOST=redis
        - DATACLAY_KV_PORT=6379
        - DATACLAY_BACKEND_ID
        - DATACLAY_BACKEND_NAME
        - DATACLAY_BACKEND_PORT=6867
        - DEBUG=true
        command: python -m dataclay.backend
        volumes:
         - ./model:/workdir/model:ro


It is important to save the dataClay classes in a folder called ``model`` to make it accessible by the backend.
In more complex deployments, the classes will be packaged in the docker image, or installed  after the deployment
using ``pip``, or other tools.