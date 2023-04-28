
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
   compile-redis


dataClay is a distributed data store that enables applications to store and access objects
in the same format they have in memory, and executes object methods within the data store. 
These two main features accelerate both the development of applications and their execution.


Installing
----------

dataclay can be installed with `pip <https://pip.pypa.io>`_

.. code-block:: console

   $ pip install dataclay


Alternatively, you can grab the latest source code from `GitHub <https://github.com/bsc-dom/dataclay>`_:

.. code-block:: console

   $ git clone https://github.com/bsc-dom/dataclay.git
   $ cd dataclay
   $ pip install .

Usage
-----

The :doc:`user-guide` is the place to go to learn how to use the library and
accomplish common tasks. The more in-depth :doc:`advanced-usage` guide is the place to go for lower-level tweaking.

The :doc:`reference/index` documentation provides API-level documentation.

Deployment
----------

The :doc:`deployment` guide provides information on how to deploy dataClay in different scenarios.

License
-------

dataClay is made available under the BSD License. For more details, see `LICENSE.txt <https://github.com/bsc-dom/dataclay/blob/main/LICENSE.txt>`_.

Contributing
------------

We happily welcome contributions, please see :doc:`contributing` for details.


