Alien Objects
=============

.. warning::

    This feature is experimental. The API is subject to change and it has **not** been thoroughly tested
    across a variety of classes, libraries and environments. Use at your own risk.

The full potential of dataClay can be achieved through defining DataClayObject classes. These classes have
the complete feature set offered by the dataClay storage system and they are highly flexible and can be
customized to almost every situation.

However, there are scenarios in which there are legacy data structures (or builtins) used by the application;
in those scenarios, reimplementing all the data model may not be ideal. In these cases, the application can use the 
:class:`~dataclay.alien.AlienDataClayObject` class (which inherits from :class:`~dataclay.DataClayObject`).


Creating an AlienDataClayObject
-------------------------------

A :class:`~dataclay.alien.AlienDataClayObject` instance is created with the following code:

.. code-block:: python

    import numpy as np

    from dataclay import AlienDataClayObject

    # initialization, application code, etc.

    a = np.array(...)
    a = AlienDataClayObject(a)

At this point, the object ``a`` is a :class:`~dataclay.alien.AlienDataClayObject`. This object can be used as a regular numpy array, but
it can also be stored in the dataClay storage system. Once it is persisted, all its methods will be available
as active methods (running in the dataClay backend).

To persist the instance, use the method :meth:`~dataclay.DataClayObject.make_persistent`.

Using an AlienDataClayObject
-----------------------------

A :class:`~dataclay.alien.AlienDataClayObject` instance behaves similarly to the underlying instance, it works as a
kind of proxy. There are certain limitations, but most getter and setter operations will work as expected (being
transparently forwarded to the underlying object in the backend). Same with its methods, which will be interpreted as
active methods and executed in the backend.

AlienDataClayObject subtypes
----------------------------

When instantiating an AlienDataClayObject, the type of the object is dynamically generated. The resulting type is 
stored in the metadata of the object. In the previous example, ``type(a)`` is ``AlienDataClayObject[numpy.ndarray]``.
This type inherits from DataClayObject, so you can rely on ``isinstance`` and most mechanisms of the 
:class:`~dataclay.dataclay_object.DataClayObject` can be used normally.

Using builtins
--------------

You can use AlienDataClayObject with builtins, such as lists, dictionaries, etc. The following example shows how to use
AlienDataClayObject with a list:

.. code-block:: python

    from dataclay import AlienDataClayObject

    # initialization, application code, etc.

    a = [1, 2, 3]
    a = AlienDataClayObject(a)

    # Persist the object
    a.make_persistent()

    # Now, a behaves as a regular list, but this method 
    # runs within the dataClay storage system
    a.append(4)

    print(len(a))

Note that the type of this object ``a`` is ``AlienDataClayObject[builtins.list]``.
