import pytest

from dataclay.contrib.modeltest.family import Family, Person
from dataclay.exceptions import DataClayException


def test_Owner_is_allowed(client):
    person = Person("Alex", 25)
    person.make_persistent(alias="test_Owner_is_allowed")
    person.add_year()
    person.age = 26
    assert person.age is 26
    person.delete_alias("test_Owner_is_allowed")
