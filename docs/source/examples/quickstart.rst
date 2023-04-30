Quickstart
==========

`This example <https://github.com/bsc-dom/dataclay/tree/main/examples/quickstart>`_ allows to deploy 
a minimal dataClay instance tu run all commands from the :doc:`../user-guide` side-by-side.

Prerequisits
------------

* Have `docker engine <https://docs.docker.com/engine/install/ubuntu/>`_ installed.
* Hava dataClay installed with ``python3 -m pip install dataclay``.
* Clone the repository with ``git clone https://github.com/bsc-dom/dataclay.git`` 

Deployment
----------

* Navigate to the example folder with ``cd dataclay/examples/quickstart``.

| quickstart
| ├── model
| │   ├── company.py
| ├── docker-compose.yml
| └── script.py

* Deploy dataClay with ``docker compose up -d``.

Execution
---------

* Run the `script.py`_ in a python interactive shell ``python3 -i script.py``. 

The `script.py`_ will only import the `Employee <company.py>`_ and `Company <company.py>`_ classes,
and start a new client session that should connect to the dataClay instance
that was deployed with ``docker compose``.

.. literalinclude:: /../../examples/quickstart/script.py
   :language: python
   :caption: script.py


Now we can start executing the :doc:`../user-guide` commands:

.. code-block:: python

    >>> employee = Employee("John", 1000.0)
    >>> employee.make_persistent()

.. _script.py: https://github.com/bsc-dom/dataclay/tree/main/examples/quickstart/script.py
.. _company.py: https://github.com/bsc-dom/dataclay/tree/main/examples/quickstart/model/company.py
