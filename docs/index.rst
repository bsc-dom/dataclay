
dataClay
========

.. toctree::
   :hidden:
   :caption: Getting Started

   user-guide
   main-concepts
   alien-objects
   advanced-usage 
   examples/index

.. toctree::
   :hidden:
   :caption: Deployment

   deployment/envvars
   deployment/management
   deployment/proxy
   deployment/docker-deployment
   deployment/hpc-manual-deployment
   deployment/compile-redis

.. toctree::
   :hidden:
   :caption: Release Notes

   releasenotes/3-x
   releasenotes/4-x

.. toctree::
   :hidden:
   :caption: API

   reference/index
   contrib/index

.. toctree::
   :hidden:
   :caption: Developers

   contributing


dataClay is a distributed data store that enables applications to store and access objects
in the same format as they have in memory and executes object methods within the data store. 
These two main features accelerate both the development of applications and their execution.


Installation
------------

To install dataClay, you can use `pip <https://pip.pypa.io>`_:

.. code-block:: console

   $ pip install dataclay


Alternatively, you can obtain the latest source code from `GitHub <https://github.com/bsc-dom/dataclay>`_:

.. code-block:: console

   $ git clone https://github.com/bsc-dom/dataclay.git
   $ cd dataclay
   $ pip install .

Usage
-----

The :doc:`user-guide` is the primary resource for learning how to use the library and
accomplish common tasks. For lower-level tweaking, refer to the :doc:`advanced-usage` guide.

The :doc:`reference/index` documentation provides API-level documentation.

Deployment
----------

The **DEPLOYMENT** section includes multiple scenarios. If you are not sure, you may want to start
with the :doc:`deployment/docker-deployment`.

License
-------

dataClay is licensed under the BSD License. For more information, refer to the `LICENSE.txt <https://github.com/bsc-dom/dataclay/blob/main/LICENSE.txt>`_.

Contributing
------------

We welcome contributions to dataClay. Please see the :doc:`contributing` for more details.


