from dataclay import Client, StubDataClayObject

client = Client(host="127.0.0.1")
client.start()

# Instantiate the stubs of remote classes
PersonStub = StubDataClayObject["model.family.Person"]
DogStub = StubDataClayObject["model.family.Dog"]

# Create a Person and a Dog from the stubs
person = PersonStub(name="Alice", age=30)
dog = DogStub(name="Rex", age=5)

# Check the person and dog are created correctly
assert person._dc_is_registered is True
assert person.name == "Alice"
assert person.age == 30
assert dog._dc_is_registered is True
assert dog.name == "Rex"
assert dog.age == 5

# Check get and set attribute of the person
assert person.name == "Alice"
assert person.age == 30
person.age = 31
assert person.age == 31

# Check calling activemethod of the person
person.add_year()
assert person.age == 32

# Set the dog to the person
person.dog = dog

# Check the dog is set correctly
assert person.dog.name == "Rex"
assert person.dog.age == 5

# Add alias to the person
person.add_alias("person_alias")

# Get the person by alias
person_by_alias = PersonStub.get_by_alias("person_alias")

# Check the person is the same as the original
assert person_by_alias == person
