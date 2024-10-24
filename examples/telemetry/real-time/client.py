from dataclay import Client
from dataclay.config import settings
from dataclay.contrib.modeltest.family import Family, Person

settings.tracing = True

client = Client(host="127.0.0.1")
client.start()

# family = Family()
# family.make_persistent("Smith")

person = Person("Marc", 24)
person.make_persistent()
# family.add(person)

# assert family is Family.get_by_alias("Smith")

# Family.delete_alias("Smith")
