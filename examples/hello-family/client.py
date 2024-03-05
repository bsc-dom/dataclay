from model.family import Family, Person

from dataclay import Client

# DC_HOST should be pass as environment variable
client = Client(host="127.0.0.1", username="testuser", password="s3cret", dataset="testdata")
client.start()

print("Hello1")

try:
    family = Family.get_by_alias("myfamily2")
except Exception:
    family = Family()
    family.make_persistent(alias="myfamily2")

person = Person("Marc", 24)
family.add(person)
print("Hello2")
print(family)
