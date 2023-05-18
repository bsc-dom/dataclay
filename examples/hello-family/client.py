from model.family import Family, Person

from dataclay import Client

# DC_HOST should be pass as environment variable
client = Client(username="testuser", password="s3cret", dataset="testdata")
client.start()

try:
    family = Family.get_by_alias("myfamily")
except Exception:
    family = Family()
    family.make_persistent(alias="myfamily")

person = Person("Marc", 24)
family.add(person)
print(family)
