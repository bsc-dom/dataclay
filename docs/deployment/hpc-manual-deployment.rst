PyCOMPSs and dataClay for HPC
=============================

This page describes, with illustrative purposes, the steps to follow in order
to reach a deployment of PyCOMPSs & dataClay into an HPC cluster.

If you want to use PyCOMPSs and dataClay in an HPC cluster, you will probably
want to deploy the different parts manually (instead of using a more quick and
easy solution such as containers). The exact deployment will depend
on your HPC cluster, the software installed and so on. This page does not aim
to be a comprehensive instruction for any environment, but instead to outline
the main steps and some pitfalls of this process.

Pre-dependencies
----------------

Python
~~~~~~

For HPC, it makes sense to use the 
`Intel Distribution for Python <https://www.intel.com/content/www/us/en/developer/tools/oneapi/distribution-for-python.html>`_.
If you already have an up-to-date version of Python that you want to use, just
skip this step.

To install Python, just grab the shell script from intel website and run it.
At the moment of writing this documentation, it is called **Stand-Alone 
Version** and it installs Python 3.9. No elevated permissions required.

Java
~~~~

This is a COMPSs dependency. Just make sure that Java is installed in your
machine. If Java is not available, install it in your home or ask a system
administrator to install it. This step is out of the scope of this general
example.

Boost C++ libraries
~~~~~~~~~~~~~~~~~~~

This is a COMPSs dependency. There are more dependencies and you may want to go
to the `COMPSs documentation <https://compss-doc.readthedocs.io/en/stable/Sections/01_Installation.html>`_
for further information on the prerequisites. However, our experience has shown
that this is one of the prerequisites that you will most likely be missing.
That's why we decided to show how to install this specific package.

To install Boost C++ libraries, download the `current release <https://www.boost.org/users/download/>`_
and extract them to the machine. Then build and install as follows::

    $ ./bootstrap.sh --prefix=$HOME/local
    $ ./b2 install

Redis
~~~~~

See :doc:`compile-redis`

Create a virtual environment
----------------------------

Optional, but highly recommended::

    $ intel/oneapi/intelpython/python3.9/bin/python -m venv path/to/venv

Of course, you will need to change the path to your Python binary
appropriately. And also change the path to the destination venv, which will
be created after running this command.

Activate the virtual environment.

Install PyCOMPSs
----------------

The *proper* way to install it is a bit fuzzy. Our experience relies in the
``BOOST_INCLUDE`` undocumented environment variable and the installation can
be performed with the following command::

    $ BOOST_INCLUDE="$HOME/local/include" \
      JAVA_HOME=/usr/lib/jvm/java-.../ \
      pip install pycompss

Change the paths according to your environment. If you have Boost C++ libraries
installed system-wide, you don't need to include the ``BOOST_INCLUDE`` envvar.

This command is long, as it is compiling stuff under the hood, but it should
eventually finish. You can check that it is installed with the following::

    $ python -m pycompss
    usage: python -m pycompss [-h] [{run,enqueue}] ...

Otherwise, you will receive a ``No module named pycompss``.

Install dataClay
----------------

You can use ``pip`` direcly::

    $ pip install dataclay

Or, if you need to use a bleeding edge version of dataClay, install from GitHub::

    $ pip install git+https://github.com/bsc-dom/dataclay.git

Or, if you are a dataClay developer who is using a custom codebase::

    $ pip install -e /path/to/dataclay/
