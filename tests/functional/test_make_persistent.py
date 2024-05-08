import pytest

from dataclay.contrib.modeltest.family import Dog, Family, Person
from dataclay.contrib.modeltest.test_remote import TestMakePersistent


def test_make_persistent_basic(client):
    """Test a simple make_persistent call"""
    person = Person("Marc", 24)
    assert person._dc_is_registered == False

    person.make_persistent()
    assert person._dc_is_registered == True
    assert person.name == "Marc"
    assert person.age == 24

    person.age = 55
    assert person.age == 55


def test_make_persistent_recursive(client):
    """
    By default, make_persistent is called recursively to all
    dataclay object attributes
    """
    family = Family()
    person = Person("Marc", 24)
    dog = Dog("Rio", 5)
    family.add(person)
    person.dog = dog
    assert person._dc_is_registered == False
    assert dog._dc_is_registered == False

    family.make_persistent()
    assert person._dc_is_registered == True
    assert person == family.members[0]
    assert dog._dc_is_registered == True
    assert dog == person.dog


def test_make_persistent_cycle(client):
    """
    A call to make_persistent should work even when there
    is a cycle relation between dataclay objects
    """
    person_1 = Person("Marc", 24)
    person_2 = Person("Alice", 21)
    person_1.spouse = person_2
    person_2.spouse = person_1
    person_1.make_persistent()

    assert person_1._dc_is_registered == True
    assert person_2._dc_is_registered == True
    assert person_1 == person_2.spouse
    assert person_2 == person_1.spouse


def test_make_persistent_backend_id(client):
    """
    Specify the backend to store the object
    """
    backend_ids = list(client.get_backends())

    person_1 = Person("Marc", 24)
    person_1.make_persistent(backend_id=backend_ids[0])
    person_2 = Person("Alice", 21)
    person_2.make_persistent(backend_id=backend_ids[1])

    assert person_1._dc_meta.master_backend_id == backend_ids[0]
    assert person_2._dc_meta.master_backend_id == backend_ids[1]


def test_make_persistent_already_registered(client):
    """
    Trying to make_persistent and already persistent object, will
    move the object to the specified backend and add a new alias
    """
    backend_ids = list(client.get_backends())
    person = Person("Marc", 24)

    person.make_persistent(backend_id=backend_ids[0])
    person.sync()  # Sync to update object metadata
    assert person._dc_meta.master_backend_id == backend_ids[0]

    person.make_persistent(
        alias="test_make_persistent_already_registered", backend_id=backend_ids[1]
    )
    person.sync()  # Sync to update object metadata
    assert person._dc_meta.master_backend_id == backend_ids[1]
    assert "test_make_persistent_already_registered" in person.get_aliases()


def test_persistent_references(client):
    """
    Trying to make_persistent and object with persistent references
    """
    person = Person("Marc", 24)
    person.make_persistent()
    family = Family(person)
    assert family._dc_is_registered == False

    family.make_persistent()
    assert family._dc_is_registered == True
    assert person == family.members[0]


# Remote methods


def test_remote_automatic_register(client):
    test_remote_method = TestMakePersistent()
    test_remote_method.make_persistent()
    test_remote_method.test_remote_automatic_register()


def test_remote_make_persistent(client):
    test_remote_method = TestMakePersistent()
    test_remote_method.make_persistent()
    test_remote_method.test_remote_make_persistent()


def test_remote_make_persistent_alias(client):
    test_remote_method = TestMakePersistent()
    test_remote_method.make_persistent()
    test_remote_method.test_remote_make_persistent_alias()


def test_remote_make_persistent_backend(client):
    test_remote_method = TestMakePersistent()
    test_remote_method.make_persistent()
    test_remote_method.test_remote_make_persistent_backend()
