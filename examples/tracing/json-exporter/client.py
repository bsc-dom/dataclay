from dataclay import Client

# from dataclay.config import settings
from dataclay.contrib.modeltest.family import Family, Person

# settings.tracing = True

client = Client()
client.start()

try:
    family = Family.get_by_alias("myfamily")
except Exception:
    family = Family()
    family.make_persistent(alias="myfamily")

person = Person("Marc", 24)
family.add(person)
print(family)
