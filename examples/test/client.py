from dataclay import Client
from dataclay.contrib.modeltest.family import Person
from dataclay.runtime import get_runtime

client = Client(host="127.0.0.1")
client.start()

runtime = get_runtime()
backend_clients = runtime.backend_clients

for backend_client in backend_clients:
    print(backend_client)


# person = Person.get_by_alias("Alice")
person = Person(name="Alice", age=33)
person.make_persistent()

person.add_year()
