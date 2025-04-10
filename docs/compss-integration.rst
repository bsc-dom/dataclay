PyCOMPSs Integrated Environment
===============================

This example demonstrates how to integrate **PyCOMPSs** and **dataClay** using Docker Compose. It also supports optional components such as **dislib** and **DDS**, providing a reproducible and configurable environment for testing and development.

**Example location in repository:**  
``dataclay/examples/compss-local/``

This directory includes Docker Compose configurations and scripts that help set up and run a distributed environment where **dataClay** and **PyCOMPSs** can interoperate.

Two environments are provided:

- ``docker-compose.yml``: Runs the **latest production versions** of all components using prebuilt images from Docker Hub.
- ``docker-compose.dev.yml``: Runs the **development versions** of `dataClay` and `dislib` for contributors testing local changes.



Running with Production Images
------------------------------

To run the environment with the **latest production versions** of `dataClay`, `dislib`, and other components:

.. code-block:: bash

   docker compose up

Once the stack is running, you can access the `compss` container and run an example:

.. code-block:: bash

   docker compose exec compss /bin/bash
   cd ~/examples/kmeans
   ./run_with_dataClay.sh

.. note::

   The first time you execute this command, Docker may need to pull and build several images, which can take some time.



Running with Development Versions
---------------------------------

To use your **local development versions** of `dataClay` and `dislib`, run the stack with the development Compose file:

.. code-block:: bash

   docker compose -f docker-compose.dev.yml up

This setup is intended for developers and contributors working on improving or testing changes to `dataClay`, `dislib`, or `PyCOMPSs`.

Setting up dislib for Development
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To enable a local version of `dislib` within the development environment:

1. Clone the `dislib` repository if you haven't already.
2. Create a symbolic link to your local `dislib` repository in the expected location:

   .. code-block:: bash

      ln -s /path/to/your/dislib dataclay/examples/compss-local/components/compss/dislib

.. warning::

   The directory ``dataclay/examples/compss-local/components/compss/dislib`` is **not tracked by git**, so you will need to recreate the symbolic link each time you set up the environment on a new machine.

This step ensures your local changes to `dislib` are used inside the running container.


Using Jupyter Notebook Interface
--------------------------------

You can also test and explore the examples interactively through a Jupyter Notebook:

1. Start the stack using either of the Compose files:

   .. code-block:: bash

      docker compose up

   or

   .. code-block:: bash

      docker compose -f docker-compose.dev.yml up

2. Once the stack is up and running, open your browser and navigate to:

   ``http://localhost:8888``

3. Use the notebook interface to navigate to the examples directory and experiment with the provided code.

---

This example is an excellent starting point to explore how **dataClay** can work with **PyCOMPSs** and **dislib** to manage distributed, persistent, and parallel computation environments.
