Virtual Objects
===============

.. warning::

    This feature is experimental. The API is subject to change and it has **not** been thoroughly tested
    across a variety of classes, libraries and environments. Use at your own risk.

The full potential of dataClay can be achieved through defining DataClayObject classes. These classes have
the complete feature set offered by the dataClay storage system and they are highly flexible and can be
customized to almost every situation.

However, there are scenarios in which there are legacy data structures used by the application; in those scenarios,
reimplementing all the data model may not be ideal. In these cases, the application can use the 
:class:`~dataclay.virtual_dco.VirtualDataClayObject` class (which inherits from :class:`~dataclay.DataClayObject`).


Creating a VirtualDataClayObject
--------------------------------

A :class:`~dataclay.virtual_dco.VirtualDataClayObject` instance is created with the following code:

.. code-block:: python

    import numpy as np

    from dataclay.virtual_dco import VirtualDataClayObject

    # initialization, application code, etc.

    a = np.array(...)
    a = VirtualDataClayObject(a)

At this point, the object ``a`` is a :class:`~dataclay.virtual_dco.VirtualDataClayObject`. This object can be used as a regular numpy array, but
it can also be stored in the dataClay storage system. Once it is persisted, all its methods will be available
as active methods (running in the dataClay backend).

To persist the instance, use the method :meth:`~dataclay.DataClayObject.make_persistent`.

Using a VirtualDataClayObject
-----------------------------

A :class:`VirtualDataClayObject` instance behaves similarly to the underlying instance, it works as a kind of proxy.
There are certain limitations, but most getter and setter operations will work as expected (being transparently forwarded
to the underlying object in the backend). Same with its methods, which will be interpreted as active methods and executed
in the backend.