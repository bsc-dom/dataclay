Hello Family
============

HelloFamily is a simple application that registers a list of people info into a persistent collection
identified by an alias. Every time this application is executed, it first tries to load the collection by
its alias, and if it does not exist the application creates it. Once the collection has been retrieved,
or created, the given new person info is added to the collection and the whole set of people is
displayed.

.. note::
    This example is available in `GitHub <https://github.com/bsc-dom/dataclay/tree/main/examples/hello-family>`_.

Class definition:

.. literalinclude:: /../examples/hello-family/model/family.py
   :language: python
   :caption: family.py

Then we can deploy dataclay using docker-compose. 
Create a file docker-compose.yml and use the following docker-compose file using `docker-compose up`:

.. literalinclude:: /../examples/hello-family/docker-compose.yml
   :language: yaml
   :caption: docker-compose.yml

Then we can run the classes in the application:

.. literalinclude:: /../examples/hello-family/client.py
   :language: python
   :caption: client.py

You can observe that after several executions, the family is increasing one member at a time.