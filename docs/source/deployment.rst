Deployment
==========

The easiest way to deploy dataClay is using the provided 
`docker image <https://github.com/bsc-dom/dataclay/pkgs/container/dataclay>`_. 
You can deploy a minimal dataClay instance with the following docker-compose:

.. literalinclude:: /../../examples/quickstart/docker-compose.yml
   :language: yaml

.. note::
    All dataClay classes must be saved in the ``model`` folder to allow access by the backend.
    In more complex deployments, the classes will be packaged in the docker image, or installed  after the deployment
    using ``pip``, or something similar.

Account Managment
-----------------

First export the following environment variables with the corresponding value::

    export DATACLAY_METADATA_HOSTNAME=127.0.0.1

To create a new account::

    python3 -m dataclay.metadata.cli new_account john s3cret

To create a new dataset::

    python3 -m dataclay.metadata.cli new_dataset john s3cret mydataset
