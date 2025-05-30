Contributing
============

The dataClay distributed data store is a 
`BSC <https://www.bsc.es/research-and-development/software-and-apps/software-list/dataclay>`_
project under the `BSD License <https://github.com/bsc-dom/dataclay/blob/main/LICENSE.txt>`_
and we happily accept contributions.

If you wish to add a new feature or fix a bug:

#. `Check for open issues <https://github.com/bsc-dom/dataclay/issues>`_ or open
   a new issue to start a discussion around a feature idea or a bug. Issues labeled
   as *Contributor Friendly* are ideal for individuals who are not yet familiar with
   the codebase.
#. Fork the `dataclay repository on Github <https://github.com/bsc-dom/dataclay>`_
   to start making your changes.
#. Write a test which shows that the bug was fixed or that the feature works
   as expected.
#. Format your changes with `Black <https://black.readthedocs.io/en/stable/>`_ using the
   command `nox -s format` and lint your changes using the command `nox -s lint`.
#. Send a pull request and follow up with the maintainer until it gets merged and published.

.. #. Add a `changelog entry
..    <https://github.com/bsc-dom/dataclay/blob/main/changelog/README.rst>`__.

Setting up your development environment
---------------------------------------

To set up your development environment, you will need `nox`_ installed on your machine:

.. code-block:: console

   $ python -m pip install --user --upgrade nox

You wll also need to have `docker engine <https://docs.docker.com/engine/install/ubuntu/>`_ installed 
for `nox`_ to use `pytest-docker <https://pypi.org/project/pytest-docker/>`_.

Install dataClay in editable mode with the ``dev`` extra requirement:

.. code-block:: console

   $ pip install -e .[dev,telemetry]

.. note::
   It is necessary to use the ``--recurse-submodules`` option to clone the repository, as it contains
   submodules that are required for the installation.

Compiling Protocol Buffers
~~~~~~~~~~~~~~~~~~~~~~~~~~

You usually don't need to compile Protocol Buffers manually. However, you **should recompile** them in the following cases:

- You've made changes to any of the `.proto` files.
- The gRPC or `protobuf` version used in the project has changed.

To compile the protobuf definitions, run:

.. code-block:: console

   $ ./compile_protos.py

This will regenerate the gRPC Python bindings used by dataClay.

Running the tests
-----------------

When running the test suite, we use external dependencies, multiple interpreters, and code coverage analysis. 
Our `noxfile.py <https://github.com/bsc-dom/dataclay/blob/main/noxfile.py>`_ file handles much of this for you:

.. code-block:: console

   $ nox
  

.. _nox: https://nox.thea.codes/en/stable/