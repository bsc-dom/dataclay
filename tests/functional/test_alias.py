from dataclay import api
from dataclay.exceptions import *

import pytest
from model.family import Family, Person
from utils import init_client, mock_env_client


def test_get_by_alias(init_client):
    person = Person("Marc", 24)
    person.make_persistent(alias="test_get_by_alias")
    assert person.get_alias() == "test_get_by_alias"
    assert person == Person.get_by_alias("test_get_by_alias")


def test_delete_alias(init_client):
    person = Person("Marc", 24)
    person.make_persistent("test_delete_alias")
    assert person.get_alias() == "test_delete_alias"

    Person.delete_alias("test_delete_alias")
    assert person.get_alias() == None
    with pytest.raises(DataClayException) as excinfo:
        Person.get_by_alias("test_delete_alias")
    assert "does not exist" in str(excinfo.value)


def test_same_alias(init_client):
    person_1 = Person("Marc", 24)
    person_2 = Person("Alice", 21)
    with pytest.raises(DataClayException) as excinfo:
        person_1.make_persistent("test_same_alias")
        person_2.make_persistent("test_same_alias")
    assert "already exist" in str(excinfo.value)


def test_change_alias(init_client):
    person = Person("Marc", 24)
    person.make_persistent("test_change_alias")
    assert person == Person.get_by_alias("test_change_alias")
