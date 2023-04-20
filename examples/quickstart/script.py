from model.family import Family, Person

from dataclay import client

client = client(host="127.0.0.1", username="testuser", password="s3cret", dataset="testuser")
client.start()

try:
    family = Family.get_by_alias("myfamily")
except Exception:
    family = Family()
    family.make_persistent(alias="myfamily")

person = Person("Marc", 24)
family.add(person)
print(family)
