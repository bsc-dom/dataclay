Advanced Usage
==============

.. currentmodule:: dataclay

This guide will cover some of the more advanced features of dataClay.

Move Object
-----------

Persistent objects can be moved from one backend to another with :meth:`move() <DataClayObject.move>`::

    # Get a list of available backend ids
    backend_ids = list(client.get_backends())

    # Move the object to the first backend id
    employee.move(backend_ids[0])


By default, only the current object will be moved. However, by passing ``recursive=True`` 
to :meth:`move() <DataClayObject.move>`, all objects reachable from the current object,
that are owned by the same backend, will be moved as well::

    backend_ids = list(client.get_backends())

    employee = Employee("John", 1000.0)
    company = Company("ABC", employee)

    # Register employee and company in the same backend
    company.make_persistent(backend_id=backend_ids[0])

    # Move company to another backend
    company.move(backend_ids[1], recursive=True)

    # employee has also moved to the same backend as company
    person_1.name  # forcing update of the backend_id
    assert employee._dc_backend_id == backend_ids[1]

But referenced objects owned by another backend will not be moved::

    backend_ids = list(client.get_backends())

    employee = Employee("John", 1000.0)
    company = Company("ABC", employee)

    # Register employee in backend 0 and company in backend 1
    employee.make_persistent(backend_id=backend_ids[0])
    company.make_persistent(backend_id=backend_ids[1])

    # Move company to backend 2
    company.move(backend_ids[2], recursive=True)

    # employee is still in backend 0
    person_1.name  # forcing update of the backend_id
    assert employee._dc_backend_id == backend_ids[0]

.. Replicas
.. --------

.. Federation
.. ----------

Versioning
----------

Versioning is a feature of dataClay objects for parallel computing. It allows to create
different versions of the same object, modify them independently,
and consolidate one version to all previous versions and back to the original dataClay object.

To create a new version we can call :meth:`new_version() <DataClayObject.new_version>`, 
and consolidate it with :meth:`consolidate_version() <DataClayObject.consolidate_version>`::

    employee = Employee("John", 1000.0)
    employee.make_persistent()

    # Create a new version of the object
    employee_v1 = employee.new_version()

    # Modify the new version
    employee_v1.salary = 2000.0

    # Consolidate the new version
    employee_v1.consolidate_version()

    # The original object has been updated
    assert employee.salary == 2000.0

It is also possible to create versions from other versions::

    employee = Employee("John", 1000.0)
    employee.make_persistent()

    # Create a new version of the object
    employee_v1 = employee.new_version()

    # Create a second version from the first one
    employee_v2 = employee_v1.new_version()

    # Modify the second version
    employee_v2.salary = 2000.0

    # Consolidate the second version
    employee_v2.consolidate_version()

    # The original object and the first version had been updated
    assert employee.salary == 2000.0
    assert employee_v1.salary == 2000.0


.. example with compss @task