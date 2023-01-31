import pytest
from model.family import Family, Person

from dataclay.exceptions import *


def test_get_by_alias(start_client):
    person = Person("Marc", 24)
    person.make_persistent(alias="test_get_by_alias")
    assert person == Person.get_by_alias("test_get_by_alias")
    Person.delete_alias("test_get_by_alias")


def test_delete_alias(start_client):
    person = Person("Marc", 24)
    person.make_persistent("test_delete_alias")

    Person.delete_alias("test_delete_alias")
    with pytest.raises(DataClayException) as excinfo:
        Person.get_by_alias("test_delete_alias")
    assert "does not exist" in str(excinfo.value)


def test_same_alias(start_client):
    person_1 = Person("Marc", 24)
    person_2 = Person("Alice", 21)
    with pytest.raises(DataClayException) as excinfo:
        person_1.make_persistent("test_same_alias")
        person_2.make_persistent("test_same_alias")
    assert "already exist" in str(excinfo.value)


def test_change_alias(start_client):
    pass
