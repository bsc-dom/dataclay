from dataclay import Client
from dataclay.contrib.modeltest.family import Family, Person

client = Client()
client.start()

family = Family()
family.make_persistent("Smith")

person = Person("Marc", 24)
family.add(person)

person.name = "Alice"
print(family)

person_2 = Family.get_by_alias("Smith").members[0]

Family.delete_alias("Smith")

assert person is person_2
client.stop()
