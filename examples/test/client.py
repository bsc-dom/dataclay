from dataclay import Client
from dataclay.contrib.modeltest.family import Person

client = Client(host="127.0.0.1")
client.start()

person = Person(name="Alice", age=33)
# person.make_persistent("Alice")