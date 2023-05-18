Quickstart
==========

`This example <https://github.com/bsc-dom/dataclay/tree/main/examples/quickstart>`_ allows to quickly deploy dataClay
and run all commands from the :doc:`../user-guide`.

Prerequisits
------------

* Have `docker engine <https://docs.docker.com/engine/install/ubuntu/>`_ installed.
* Hava dataClay installed::
   
   python3 -m pip install dataclay

* Clone the repository::
   
   git clone https://github.com/bsc-dom/dataclay.git 

Deployment
----------

* Navigate to the ``quickstart`` folder::

   cd dataclay/examples/quickstart

The folder should contain the following files:

.. code-block:: text

    quickstart
    ├── model
    │   └── company.py
    ├── docker-compose.yml
    └── client.py

* Deploy dataClay with ``docker compose``::
   
   docker compose up -d

Execution
---------

* Run the `client.py`_ in a python interactive shell::
   
   python3 -i client.py

The `client.py`_ will only import the `Employee`_ and `Company`_ classes,
and start a new client session that should connect to the dataClay instance
that was deployed with ``docker compose``.

.. literalinclude:: /../examples/quickstart/client.py
   :language: python
   :caption: client.py


Now we can start executing the :doc:`../user-guide` commands:

.. code-block:: python

    >>> employee = Employee("John", 1000.0)
    >>> employee.make_persistent()

.. _client.py: https://github.com/bsc-dom/dataclay/tree/main/examples/quickstart/client.py
.. _Employee: https://github.com/bsc-dom/dataclay/tree/main/examples/quickstart/model/company.py
.. _Company: https://github.com/bsc-dom/dataclay/tree/main/examples/quickstart/model/company.py


Don't forget to stop the dataClay instance when you are done:

.. code-block:: console

   $ docker compose down