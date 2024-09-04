import pytest

from dataclay.contrib.modeltest.family import Dog, Family, Person
from dataclay.contrib.modeltest.remote import ActivemethodTestClass


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


def test_activemethod_nested_getattribute(client):
    """
    An activemethod that calls multiple getattribute inside
    """
    family = Family()
    family.make_persistent()

    # Technically, there is a change that all the following objects
    # are made persistent in a single backend and thus this test
    # may be inconclusive. The chance is (1/n_backends)^(n_objects - 1).

    # Increment either n to feel safer, or change the make_persistent
    # to be deterministically correct.

    person = Person("Marc", 24)
    person.make_persistent()
    family.add(person)
    person = Person("Anna", 24)
    person.make_persistent()
    family.add(person)
    dog = Dog("Duna", 6)
    dog.make_persistent()
    family.add(dog)
    dog = Dog("Luna", 6)
    dog.make_persistent()
    family.add(dog)

    family_str = str(family)  # This calls the __str__ activemethod
    assert "Marc" in family_str
    assert "Anna" in family_str
    assert "Duna" in family_str
    assert "Luna" in family_str


# Remote methods


def test_remote_activemethod(client):
    """
    Test activemethod in a remote object
    """
    test_activemethod = ActivemethodTestClass()
    test_activemethod.make_persistent()
    test_activemethod.test_activemethod()
