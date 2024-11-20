from dataclay import Client
from dataclay.contrib.modeltest.family import Family, Person
from dataclay.exceptions import DataClayException

# DC_HOST should be pass as environment variable
client = Client(proxy_host="127.0.0.1", username="test", dataset="test")
client.start()

try:
    family = Family.get_by_alias("Simpson")
    print("Found the Simpson family in the system.")

    print("The family contains %d members:" % len(family.members))
    for person in family.members:
        print(" - %s, age %d" % (person.name, person.age))

except DataClayException:
    print("The Simpson family is not in the system.")

    print("Creating the family...")
    family = Family()
    family.make_persistent(alias="Simpson")
    print("Adding Marge Simpson...")
    person = Person("Marge", 24)
    family.add(person)
    print("Adding Homer Simpson...")
    person = Person("Homer", 26)
    family.add(person)

    print("The family has been created and populated.")
