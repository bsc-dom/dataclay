from dataclay import StubDataClayObject


def test_stub_object_instantitation(client):
    """Test the instantiation of a stub object"""
    PersonStub = StubDataClayObject["dataclay.contrib.modeltest.family.Person"]
    person = PersonStub(name="Alice", age=30)

    assert person._dc_is_registered is True
    assert person.name == "Alice"
    assert person.age == 30


def test_stub_object_get_set_attribute(client):
    """Test the get and set of an attribute of a stub object"""
    PersonStub = StubDataClayObject["dataclay.contrib.modeltest.family.Person"]
    person = PersonStub(name="Alice", age=30)

    assert person.name == "Alice"
    assert person.age == 30

    person.age = 31

    assert person.age == 31


def test_stub_object_put_stub_object(client):
    """checking if the client can put a Stub Dog instance in a Person"""
    PersonStub = StubDataClayObject["dataclay.contrib.modeltest.family.Person"]
    DogStub = StubDataClayObject["dataclay.contrib.modeltest.family.Dog"]
    person = PersonStub(name="Alice", age=30)
    dog = DogStub(name="Rex", age=5)
    person.dog = dog

    assert person.dog.name == "Rex"
    assert person.dog.age == 5


def test_stub_object_method_call(client):
    """Test the call of a method of a stub object"""
    PersonStub = StubDataClayObject["dataclay.contrib.modeltest.family.Person"]
    person = PersonStub(name="Alice", age=30)

    person.add_year()

    assert person.age == 31


def test_stub_object_get_by_alias(client):
    """Test the get_by_alias method of a stub object"""
    PersonStub = StubDataClayObject["dataclay.contrib.modeltest.family.Person"]
    person = PersonStub(name="Alice", age=30)
    person.make_persistent(alias="test_stub_object_get_by_alias")

    person = PersonStub.get_by_alias("test_stub_object_get_by_alias")

    assert person._dc_is_registered is True
    assert person.name == "Alice"
    assert person.age == 30


def test_stub_object_getstate_setstate(client):
    """Test the __getstate__ and __setstate__ methods of a stub object"""
    TextReaderStub = StubDataClayObject["dataclay.contrib.modeltest.classes.TextReader"]
    text_reader = TextReaderStub("test.txt")

    assert text_reader.lineno == 0
    assert text_reader.filename == "test.txt"


def test_stub_object_new_puppy(client):
    """Test the new_puppy method of a stub object"""
    DogStub = StubDataClayObject["dataclay.contrib.modeltest.family.Dog"]
    dog = DogStub(name="Rex", age=5)
    puppy = dog.new_puppy("Bobby")

    assert puppy.name == "Bobby"
    assert puppy in dog.puppies
