Stub Objects
============

In some scenarios, it may be unfeasible to have the full data model of an object. This can be motivated
by library requirements, agile development cycles, or other reasons. In these cases, the Stub feature
allows to use dataClay objects without having the full data model locally.

.. note::
    A Stub object will always be remote. A client using Stub objects will be unable to
    have local instances of the objects.

To make use of this feature, applications can use the 
:class:`~dataclay.stub.StubDataClayObject` class (which inherits from :class:`~dataclay.DataClayObject`).


Creating a Stub
---------------

At a fundamental level, a Stub **class** is created as follows:

.. code-block:: python

    from dataclay import StubDataClayObject

    PersonStub = StubDataClayObject["dataclay.contrib.modeltest.family.Person"]

This line will create a new class, not an instance. As you can see, the Stub metaclass
needs the string representation of the class. This is a string because the client may
not have the data model locally.

.. note::

    The client **must** be initialized before creating a stub. The creation
    of the stub class needs to retrieve information regarding the properties and active methods
    available for the class --i.e., requires information from the data model. 
    And that requires communication with dataClay services.

Once the Stub class is created, instances can be created naturally:

.. code-block:: python

    p = PersonStub(name="Alice", age=30)

Note that the stub is always refering to remote objects, so there is no need to call
:meth:`~dataclay.DataClayObject.make_persistent` (Stub class do not have this method).

Assigning aliases
-----------------

To assign an alias to the object, the :meth:`~dataclay.DataClayObject.add_alias` method can be used:

.. code-block:: python

    p.add_alias("person-alice-38")

To retrieve an existing object by its alias, the :meth:`~dataclay.StubDataClayObject.get_by_alias`
method can be used (similar to the homonym :meth:`~dataclay.DataClayObject.get_by_alias`):

.. code-block:: python

    p = PersonStub.get_by_alias("person-alice-38")


Accessing properties and active methods
---------------------------------------

Getter and setter operations will work transparently, just as in any dataClay object:

.. code-block:: python

    print(p.name)  # Alice
    p.age = 31

The same applies to active methods:

.. code-block:: python

    p.add_year()

.. warning::

    Given that the client does not have the data model locally, methods cannot be run
    locally. That means that a method with no ``@activemethod`` decorator does not exist
    from the point of view of the client.