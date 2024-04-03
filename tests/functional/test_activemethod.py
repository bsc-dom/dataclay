import pytest

from dataclay.contrib.modeltest.family import Dog, Family, Person
from dataclay.contrib.modeltest.test_remote import TestActivemethod


def test_activemethod_argument_make_persistent(client):
    """
    A dataclay object is made persistent when passed as an argument
    to an activemethod of a persistent object
    """
    family = Family()
    family.make_persistent()
    person = Person("Marc", 24)
    assert person._dc_is_registered == False

    family.add(person)
    assert person._dc_is_registered == True
    assert person == family.members[0]


def test_activemethod_persistent_argument(client):
    """
    Persistent objects can be sent as activemethod arguments
    """
    family = Family()
    person = Person("Marc", 24)
    family.make_persistent()
    person.make_persistent()
    family.add(person)
    assert person == family.members[0]


def test_activemethod_defined_properties(client):
    """
    Object properties defined in class annotations are sychronized between the client and backend
    """
    person = Person("Marc", 24)
    assert person.age == 24

    person.make_persistent()
    person.add_year()
    assert person.age == 25


def test_activemethod_non_defined_properties(client):
    """
    Object properties not defined in class annotations are not synchronized between the client and backend
    """
    dog = Dog("Duna", 6)
    assert dog.dog_age == 6 * 7

    dog.make_persistent()
    dog.add_year()
    assert dog.dog_age == 6 * 7  # Age property is not synchronized
    assert dog.get_dog_age() == 7 * 7


def test_activemethod_inner_make_persistent(client):
    """
    Objects crated inside an activemethod should be made persistent
    """
    dog = Dog("Duna", 6)
    dog.make_persistent()
    puppy = dog.new_puppy("Rio")
    assert puppy._dc_is_registered == True
    assert puppy == dog.puppies[0]
    assert puppy.name == "Rio"
    assert puppy.age == 0


# Remote methods


def test_remote_activemethod(client):
    """
    Test activemethod in a remote object
    """
    test_activemethod = TestActivemethod()
    test_activemethod.make_persistent()
    test_activemethod.test_activemethod()
