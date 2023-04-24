Quickstart
==========

A Minimal Application
---------------------

**This example is available in the `examples/quickstart` folder.**

A minimal dataClay application looks something like this:

First we have to define the classes that we want to use in the application. This classes mest be available for the client and the backend. For a simple use case, save the classes to a file `family.py` inside a folder called `model`, and then create a volume in the `docker-compose.yml` file to mount the folder inside the container.

.. code-block:: python

    from dataclay import DataClayObject, activemethod

    class Person(DataClayObject):

        name: str
        age: int

        @activemethod
        def __init__(self, name, age):
            self.name = name
            self.age = age

    class Family(DataClayObject):

        members: list[Person]

        @activemethod
        def __init__(self, *args):
            self.members = list(args)

        @activemethod
        def add(self, new_member: Person):
            self.members.append(new_member)

        @activemethod
        def __str__(self) -> str:
            result = ["Members:"]
            for p in self.members:
                result.append(" - Name: %s, age: %d" % (p.name, p.age))
            return "\n".join(result)

Then we can deploy dataclay using docker-compose. Create a file docker-compose.yml and use the following docker-compose file using `docker-compose up`:

.. code-block:: yml

    version: '3.9'
    services:

    redis:
        image: redis:latest
        ports:
        - 6379:6379

    metadata-service:
        image: "ghcr.io/bsc-dom/dataclay:edge"
        depends_on:
        - redis
        ports:
        - 16587:16587
        environment:
        - DATACLAY_KV_HOST=redis
        - DATACLAY_KV_PORT=6379
        - DATACLAY_ID
        - DATACLAY_PASSWORD=s3cret
        - DATACLAY_USERNAME=testuser
        - DATACLAY_METADATA_PORT=16587
        command: python -m dataclay.metadata

    backend:
        image: "ghcr.io/bsc-dom/dataclay:edge"
        depends_on:
        - redis
        ports:
        - 6867:6867
        environment:
        - DATACLAY_KV_HOST=redis
        - DATACLAY_KV_PORT=6379
        - DATACLAY_BACKEND_ID
        - DATACLAY_BACKEND_NAME
        - DATACLAY_BACKEND_PORT=6867
        - DEBUG=true
        command: python -m dataclay.backend
        volumes:
         - ./model:/workdir/model:ro

Then we can run the classes in the application:

.. code-block:: python

    from dataclay import client
    from model.family import Person, Family

    client = client(host="127.0.0.1", username="testuser", password="s3cret", dataset="testuser")
    client.start()

    try:
        family = Family.get_by_alias("myfamily")
    except Exception:
        family = Family()
        family.make_persistent(alias="myfamily")

    person = Person("Marc", 24)
    family.add(person)
    print(family)

You can observe that after several executions, the family is increasing one member at a time.