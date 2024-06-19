Proxy service
=============

The proxy service is an optional service that the :class:`~dataclay.Client` can use to access any backend and the metadata service.
This can be useful for:

- Bypassing NATs and firewalls.
- Performing SSL termination in a single point.
- Simplifying the docker deployment procedure.
- Adding fine-grain ACL mechanisms in client connections.
- Adding other behaviors to the client connections, such as throttle, logging, etc.

The proxy service can be started with the following command:

.. code-block:: bash

    $ python -m dataclay.proxy

The following environment variables **must** be defined:

- **DATACLAY_KV_HOST**: The Redis service host.
- **DATACLAY_PROXY_MDS_HOST**: The metadata service host.

See :class:`~dataclay.config.ProxyConfig` for a comprehensive description of all the available configuration variables.

You can subclass the :class:`~dataclay.proxy.MiddlewareBase` class to define a specific behavior of the proxy service. See
the `proxy_acl example <https://github.com/bsc-dom/dataclay/tree/main/examples/proxy_acl>`_ for a more convoluted example
of how to use the proxy service with custom middleware definitions.

The gRPC calls are the ``CamelCase`` version of the APIs methods detailed in 
:class:`~dataclay.backend.api.BackendAPI` and :class:`~dataclay.metadata.api.MetadataAPI`.
