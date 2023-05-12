Contributing
============

dataClay is a `BSC <https://www.bsc.es/research-and-development/software-and-apps/software-list/dataclay>`_
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
   command `tox -e format` and lint your changes using the command `tox -e lint`.
#. Send a pull request and follow up with the maintainer until it gets merged and published.

.. #. Add a `changelog entry
..    <https://github.com/bsc-dom/dataclay/blob/main/changelog/README.rst>`__.

Setting up your development environment
---------------------------------------

To set up your development environment, you will need `tox`_ installed on your machine:

.. code-block:: console

   $ python -m pip install --user --upgrade tox

You wll also need to have `docker engine <https://docs.docker.com/engine/install/ubuntu/>`_ installed 
for `tox`_ to use `pytest-docker <https://pypi.org/project/pytest-docker/>`_.

Install dataClay in editable mode with the ``dev`` extra requirement:

.. code-block:: console

   $ pip install -e .[dev, tracing]

Running the tests
-----------------

When running the test suite, we use external dependencies, multiple interpreters, and code coverage analysis. 
Our `tox.ini <https://github.com/bsc-dom/dataclay/blob/main/tox.ini>`_ file handles much of this for you:

.. code-block:: console

   $ tox -e py310
  

.. _tox: https://tox.wiki/en/stable/