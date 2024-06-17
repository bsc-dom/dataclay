import pytest

from dataclay.contrib.modeltest.family import Family, Person
from dataclay.exceptions import DataClayException


def test_Marc_is_allowed(client):
    person = Person("Marc", 25)
    person.make_persistent(alias="test_Marc_is_allowed")
    person.add_year()
    assert person.age is 26
    person.delete_alias("test_Marc_is_allowed")


def test_Marc_is_not_allowed(client):
    person = Person("Marc", 25)
    person.make_persistent(alias="test_Marc_is_not_allowed")
    with pytest.raises(DataClayException) as excinfo:
        person.age = 26
    assert "Method SetObjectAttribute not allowed" in str(excinfo.value)
    person.delete_alias("test_Marc_is_not_allowed")
