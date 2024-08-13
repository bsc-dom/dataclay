import pytest

from dataclay.contrib.modeltest.family import Person
from dataclay.exceptions import AliasAlreadyExistError, AliasDoesNotExistError


def test_alias_already_exists(client):
    person_1 = Person("Marc", 24)
    person_2 = Person("Alice", 21)
    person_1.make_persistent("test_same_alias_error")
    with pytest.raises(AliasAlreadyExistError):
        person_2.make_persistent("test_same_alias_error")


def test_alias_does_not_exist(client):
    with pytest.raises(AliasDoesNotExistError):
        Person.get_by_alias("test_alias_does_not_exist_error")
