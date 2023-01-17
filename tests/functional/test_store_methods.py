import pytest
from model.family import Dog, Family, Person


def test_dc_put(start_client):
    person = Person("Marc", 24)
    person.dc_put("test_dc_put")
    assert person.is_registered == True
    assert person.name == "Marc"
    assert person.age == 24


def test_dc_clone(start_client):
    person = Person("Marc", 24)
    person.dc_put("test_dc_clone")
    copy = person.dc_clone()
    assert copy.name == person.name
    assert copy.age == person.age


def test_dc_clone_by_alias(start_client):
    person = Person("Marc", 24)
    person.dc_put("test_dc_clone_by_alias")
    clone = Person.dc_clone_by_alias("test_dc_clone_by_alias")
    assert clone.name == person.name
    assert clone.age == person.age


def test_dc_update(start_client):
    person = Person("Marc", 24)
    person.dc_put("test_dc_update")
    new_person = Person("Alice", 32)
    person.dc_update(new_person)
    assert person.name == new_person.name
    assert person.age == new_person.age


def test_dc_update_by_alias(start_client):
    person = Person("Marc", 24)
    person.dc_put("test_dc_update_by_alias")
    new_person = Person("Alice", 32)
    Person.dc_update_by_alias("test_dc_update_by_alias", new_person)
    assert person.name == new_person.name
    assert person.age == new_person.age
