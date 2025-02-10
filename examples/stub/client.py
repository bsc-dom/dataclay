from dataclay import Client, StubDataClayObject
from dataclay.contrib.modeltest.family import Person

client = Client(host="127.0.0.1")
client.start()

# PersonStub = StubDataClayObject["dataclay.contrib.modeltest.family.Person"]
PersonStub = StubDataClayObject[
    "dataclay.contrib.modeltest.family.Person", ["name", "age"], ["add_year"]
]

p = PersonStub(name="Alice", age=30)
# p = PersonStub.get_by_alias("Alice")


# print(p.name)  # Alice
# p.age = 31

# p.add_year()
