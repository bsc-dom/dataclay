
dataClay
========

.. toctree::
   :hidden:
   :caption: Getting Started

   user-guide
   deployment
   main-concepts
   advanced-usage 
   examples/index

.. toctree::
   :hidden:
   :caption: API

   reference/index

.. toctree::
   :hidden:
   :caption: Developers

   contributing
   .. compile-redis


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

The :doc:`deployment` guide offers information on how to deploy dataClay in different scenarios.

License
-------

dataClay is licensed under the BSD License. For more information, refer to the `LICENSE.txt <https://github.com/bsc-dom/dataclay/blob/main/LICENSE.txt>`_.

Contributing
------------

We welcome contributions to dataClay. Please see the :doc:`contributing` for more details.


