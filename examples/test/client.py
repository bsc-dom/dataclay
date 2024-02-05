from dataclay import Client
from dataclay.contrib.modeltest.family import Person

client = Client(host="127.0.0.1", username="testuser", password="s3cret", dataset="testdata")
client.start()

# person = Person.get_by_alias("Alice")
person = Person(name="Alice", age=33)
person1 = Person(name="David",age=2)

#person.make_persistent("Alice")
