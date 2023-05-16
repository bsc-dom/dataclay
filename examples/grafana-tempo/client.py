from dataclay import Client
from dataclay.conf import settings
from dataclay.contrib.modeltest.family import Dog, Family, Person

settings.DATACLAY_TRACING = True

client = Client(host="127.0.0.1", username="testuser", password="s3cret", dataset="testdata")
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
