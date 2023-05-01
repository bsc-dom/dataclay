Contributing
============

dataClay is a `BSC <https://www.bsc.es/research-and-development/software-and-apps/software-list/dataclay>`_
project under the `BSD License <https://github.com/bsc-dom/dataclay/blob/main/LICENSE.txt>`_
and we happily accept contributions.

If you wish to add a new feature or fix a bug:

#. `Check for open issues <https://github.com/bsc-dom/dataclay/issues>`_ or open
   a fresh issue to start a discussion around a feature idea or a bug. There is
   a *Contributor Friendly* tag for issues that should be ideal for people who
   are not very familiar with the codebase yet.
#. Fork the `dataclay repository on Github <https://github.com/bsc-dom/dataclay>`_
   to start making your changes.
#. Write a test which shows that the bug was fixed or that the feature works
   as expected.
#. Format your changes with black using command `$ tox -e format` and lint your
   changes using command `tox -e lint`.
#. Send a pull request and bug the maintainer until it gets merged and published.

.. #. Add a `changelog entry
..    <https://github.com/urllib3/urllib3/blob/main/changelog/README.rst>`__.

Setting up your development environment
---------------------------------------

In order to setup the development environment you need
`tox`_ installed in your machine::

  $ python -m pip install --user --upgrade tox

You wll also need to have `docker engine <https://docs.docker.com/engine/install/ubuntu/>`_ installed 
for `tox`_ to use `pytest-docker <https://pypi.org/project/pytest-docker/>`_.

Install dataClay in editable mode with the ``dev`` extra requirement::

   $ pip install -e .[dev]

Running the tests
-----------------

When running the test suite, we use external dependencies, multiple interpreters, and code coverage analysis. 
Our `tox.ini <https://github.com/bsc-dom/dataclay/blob/main/tox.ini>`_ file handles much of this for you::

  $ tox -e py310
  

.. _tox: https://tox.wiki/en/stable/