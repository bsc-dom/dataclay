User Guide
==========

.. currentmodule:: dataclay

.. note::
    You can also follow this guide by running side-by-side all the commands with the 
    :doc:`examples/quickstart` example.


Installation
------------

dataClay can be installed with `pip <https://pip.pypa.io>`_:

.. code-block:: console

  $ python -m pip install dataclay


Defining Classes
----------------

The model provider is responsible of the design and implementation of class models. 
The data structure, the methods and the relationships that the applications can use
to access and process it.

A minimal dataClay class looks something like this:

.. literalinclude:: /../examples/quickstart/model/company.py
   :language: python

All dataClay classes must inherit from :class:`DataClayObject`. 

It is required to `annotate <https://docs.python.org/3/howto/annotations.html>`_ the fields that will be persisted in dataClay. 
The rest of the fields will be ignored and will only be accessible by the local instance.

We decorate the methods with :func:`@activemethod <activemethod>` to indicate that they will be executed in dataClay 
(if the object is persistent). The rest of the methods will always be executed locally.


Connect Client
--------------

To connect to a dataClay we have to create an instance of :class:`Client` and provide the
host, username, password and dataset to connect to. You can provide it as arguments or
as environment variables:

- ``DATACLAY_METADATA_HOSTNAME``: Hostname of the dataClay instance.
- ``DATACLAY_METADATA_PORT``: Port of the dataClay instance.
- ``DC_USERNAME``: Username to connect to dataClay.
- ``DC_PASSWORD``: Password to connect to dataClay.
- ``DC_DATASET``: Dataset to connect to.

.. code-block:: python

  from dataclay import Client

  client = Client(
    host="127.0.0.1", port="16587", username="testuser", password="s3cret", dataset="testdata"
  )

We can start the connection by calling :meth:`start() <Client.start>`
and stop it with :meth:`stop() <Client.stop>`::

    client.start()
    # do something
    client.stop()

You can also use the client as a context manager::

  with client:
      # do something

Make Persistent
---------------

We can call :meth:`make_persistent() <DataClayObject.make_persistent>` on a dataClay object to make it persistent::

    employee = Employee("John", 1000.0)
    employee.make_persistent()

Then all methods decorated with :func:`@activemethod <activemethod>` will be executed in dataClay::

    payroll = employee.get_payroll(50)

And all annotated attributes will be accessed and updated in dataClay,
potentially reducing the local memory footprint::

    employee.salary = 2000.0 # Remote call
    print(employee.name, employee.salary) # Two remote calls


Assign backend
^^^^^^^^^^^^^^

Every dataClay object is owned by a backend. When calling :meth:`make_persistent() <DataClayObject.make_persistent>`
we can specify the backend where the object will be registered. If no backend is specified, the object will be
registered in a random backend.

We can get a list of backend ids with :meth:`get_backends() <Client.get_backends>`
and register a dataClay object to one of the backends::

    backend_ids = list(client.get_backends())
    employee = Employee("John", 1000.0)
    employee.make_persistent(backend_id=backend_ids[0])

Recursive
^^^^^^^^^

By default, :meth:`make_persistent() <DataClayObject.make_persistent>` will register the current object
and all the dataClay objects referenced by it in a recursive manner::

    employee = Employee("John", 1000.0)
    company = Company("ABC", employee)

    # company and employee are registered
    company.make_persistent(recursive=True)
    assert employee.is_registered

This behavior can be disabled by passing ``recursive=False`` 
to :meth:`make_persistent() <DataClayObject.make_persistent>`::

    employee = Employee("John", 1000.0)
    company = Company("ABC", employee)

    company.make_persistent(recursive=False)
    assert company.is_registered
    assert not employee.is_registered

Automatic persistence
^^^^^^^^^^^^^^^^^^^^^

When you add a new reference of a dataClay object to a persistent object, 
this will be automatically registered::

    company = Company("ABC")
    company.make_persistent()

    # New dataClay object
    employee = Employee("John", 1000.0)
    # This will register the employee in dataClay
    company.employees = [employee]

    assert employee.is_registered 
    assert employee in company.employees

However, if you mutate a persistent attribute, the change will not be reflected in dataClay::

    company = Company("ABC")
    company.make_persistent()

    employee = Employee("John", 1000.0)
    # This will NOT register the employee in dataClay
    company.employees.append(employee)

    assert not employee.is_registered
    assert employee not in company.employees

This happens because when accessing ``company.employees`` it creates a local copy of the list.
The ``append`` only updates this local copy. To update the list in dataClay, we have to assign
the new list to the attribute. This will also register the employee::

    company = Company("ABC")
    company.make_persistent()

    employee = Employee("John", 1000.0)
    employees = company.employees
    employees.append(employee)
    # This will register the employee in dataClay
    company.employees = employees

    assert employee.is_registered 
    assert employee in company.employees

.. Another option would be to create a proxy of the list.
.. A new dataClay class that contains the list.
.. Check the :doc:`example/matrix` for an example.

Alias
-----

Objects with alias are objects that have been explicitly named (much in the same way we
give names to files). Not all dataClay objects need to have an alias (a name). If an object has
an alias, we can access it by using its name. On the other hand, objects without an alias can
only be accessed by a reference from another object.

.. warning::
    The alias must be unique within the dataset. If we try to create an object
    with an alias that already exists, an exception will be raised.


To register an object with an alias, we can use the :meth:`make_persistent() <DataClayObject.make_persistent>`
method and pass the alias as the first parameter::

    employee = Employee("John", 1000.0)
    employee.make_persistent("CEO")

Then, we can retrieve the object by using :meth:`get_by_alias() <DataClayObject.get_by_alias>`::

    employee = Employee("John", 1000.0)
    employee.make_persistent("CEO")

    new_employee = Employee.get_by_alias("CEO")
    assert new_employee is employee

The alias can be removed by calling :meth:`delete_alias() <DataClayObject.delete_alias>` classmethod::

    Employee.delete_alias("CEO")

Get, Put & Update
-----------------

Previously we have been using dataClay objects in a object-oriented manner.
However, we can also use dataClay like a standard object store with
``get``, ``put`` and ``update`` methods.

We can register and object with :meth:`dc_put(alias) <DataClayObject.dc_put>`.
This method always requires an alias::

    employee = Employee("John", 1000.0)
    employee.dc_put("CEO")

And we can clone a registered object with :meth:`dc_clone() <DataClayObject.dc_clone>`::

    new_employee = employee.dc_clone()
    assert new_employee.name == employee.name
    assert new_employee is not employee

Or using :meth:`dc_clone_by_alias(alias) <DataClayObject.dc_clone_by_alias>` classmethod::
    
    new_employee = Employee.dc_clone_by_alias("CEO")

We can update a registered object from another object of the same class with :meth:`dc_update(from_object) <DataClayObject.dc_update>`::
    
    new_employee = Employee("Marc", 7000.0)
    employee.dc_update(new_employee)
    assert employee.name == "Marc"

Or with :meth:`dc_update_by_alias(alias, from_object) <DataClayObject.dc_update_by_alias>` classmethod::
    
    new_employee = Employee("Marc", 7000.0)
    Employee.dc_update_by_alias("CEO", new_employee)
