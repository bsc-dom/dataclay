from dataclay import api
import pytest
from model.family import Family, Person
from utils import init_client, mock_env_client


def test_make_persistent_basic(init_client):
    """Test a simple make_persistent call"""
    # api.init()

    person = Person("Marc", 24)
    assert person.is_persistent == False

    person.make_persistent()
    assert person.is_persistent == True
    assert person.name == "Marc"
    assert person.age == 24

    person.age = 55
    assert person.age == 55

    # api.finish()


def test_make_persistent_recursive(init_client):
    """
    By default, make_persistent is called recursively to all
    dataclay object attributes
    """
    # api.init()

    family = Family()
    person = Person("Marc", 24)
    family.add(person)
    assert person.is_persistent == False

    family.make_persistent()
    assert person.is_persistent == True
    assert person == family.members[0]

    # api.finish()


def test_make_persistent_cycle(init_client):
    """
    A call to make_persistent should work even when there
    is a cycle relation between dataclay objects
    """

    # api.init()

    person_1 = Person("Marc", 24)
    person_2 = Person("Alice", 21)
    person_1.spouse = person_2
    person_2.spouse = person_1
    person_1.make_persistent()

    assert person_1.is_persistent == True
    assert person_2.is_persistent == True
    assert person_1 == person_2.spouse
    assert person_2 == person_1.spouse
