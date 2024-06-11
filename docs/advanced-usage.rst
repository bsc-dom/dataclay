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
to :meth:`move() <DataClayObject.move>`, all objects reachable from the current object
will be moved as well::

    backend_ids = list(client.get_backends())

    employee = Employee("John", 1000.0)
    employee.make_persistent(backend_id=backend_ids[0])

    company = Company("ABC", employee)
    company.make_persistent(backend_id=backend_ids[1])

    company.move(backend_ids[2], recursive=True)

    # employee has also moved
    employee.name  # forcing update of the backend_id
    assert employee._dc_meta.master_backend_id == backend_ids[2]

By setting ``remotes=False``, the recursive option will only move referents that are local
int the same backend, ignoring referents owned by other backends.

    backend_ids = list(client.get_backends())

    employee = Employee("John", 1000.0)
    employee.make_persistent(backend_id=backend_ids[0])

    company = Company("ABC", employee)
    company.make_persistent(backend_id=backend_ids[1])

    company.move(backend_ids[2], recursive=True, remotes=False)

    # employee is still in backend 0
    employee.name  # forcing update of the backend_id
    assert employee._dc_meta.master_backend_id == backend_ids[0]

Trying to :meth:`make_persistent() <DataClayObject.make_persistent>` and already registered object
will make and underneath call to :meth:`move() <DataClayObject.move>` with ``recursive=False`` and
:meth:`add_alias() <DataClayObject.add_alias>` if the alias is provided.

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



Asynchronous Operations
-----------------------

The dataClay runtime is asynchronous by default. This means that all dataClay operations are 
executed as tasks in an event loop which is running in a separate thread. 
In the previous examples, we have seen the synchronous version of the dataClay operations,
which block the current thread until the operation is completed. This may be sufficient for
most use cases, but in some cases, it may be necessary to execute multiple operations concurrently
to improve performance for I/O-bound applications.

All DataClayObject methods have an asynchronous version that can be called using the ``await`` keyword::

    async def main():
        client = Client()
        client.start()

        # Print the available backends using the asynchronous version of the method
        print(await client.a_get_backends())

        employee_1 = Employee("John", 1000.0)
        employee_2 = Employee("Jane", 2000.0)

        # Use gather to execute multiple make_persistent concurrently
        await asyncio.gather(
            employee_1.a_make_persistent(),
            employee_2.a_make_persistent()
        )

    if __name__ == "__main__":
        asyncio.run(main())

.. example for async attribute access
.. example for async activemethod


Multithreading
--------------

When using dataClay in a multithreaded environment, it is important to ensure that the
correct context is used for each thread. This can be achieved by using the
:mod:`contextvars` module to get the current context and pass it to the thread.
The context contains the active username and dataset for the current thread.
This is important because each rpc call to a backend will contain the username and dataset
from the client.

    import contextvars

    current_context = contextvars.copy_context()

    def job(name, age):
        person = Person(name, age)
        person.make_persistent()


    with ThreadPoolExecutor() as executor:
        for i in range(10):
            future = executor.submit(current_context.run, job, f"Name{i}", i)
            print(future.result())
