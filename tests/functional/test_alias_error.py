import pytest

from dataclay.contrib.modeltest.family import Person
from dataclay.exceptions import (
    AliasDoesNotExistError,
    AlreadyExistError,
    DataClayException,
    ObjectNotRegisteredError,
)


def test_alias_already_exists(client):
    person_1 = Person("Marc", 24)
    person_2 = Person("Alice", 21)
    person_1.make_persistent("test_same_alias_error")
    with pytest.raises(AlreadyExistError) as excinfo:
        person_2.make_persistent("test_same_alias_error")
    assert "admin/test_same_alias_error already exists" in str(excinfo.value)


@pytest.mark.asyncio
async def test_alias_already_exists_async(client):
    person_1 = Person("Marc", 24)
    person_2 = Person("Alice", 21)
    await person_1.a_make_persistent("test_same_alias_error_async")
    with pytest.raises(AlreadyExistError) as excinfo:
        await person_2.a_make_persistent("test_same_alias_error_async")
    assert "admin/test_same_alias_error_async already exists" in str(excinfo.value)


def test_alias_does_not_exist(client):
    with pytest.raises(AliasDoesNotExistError) as excinfo:
        Person.get_by_alias("test_alias_does_not_exist_error")
    assert "Alias None/test_alias_does_not_exist_error does not exist" in str(excinfo.value)


@pytest.mark.asyncio
async def test_alias_does_not_exist_async(client):
    with pytest.raises(AliasDoesNotExistError) as excinfo:
        await Person.a_get_by_alias("test_alias_does_not_exist_error_async")
    assert "Alias None/test_alias_does_not_exist_error_async does not exist" in str(excinfo.value)


def test_add_alias_notRegistered(client):
    person = Person("Marc", 24)
    with pytest.raises(ObjectNotRegisteredError) as excinfo:
        person.add_alias("test_add_alias_to_non_persitent_object")
    assert "is not registered!" in str(excinfo.value)


@pytest.mark.asyncio
async def test_add_alias_notRegistered_async(client):
    person = Person("Marc", 24)
    with pytest.raises(ObjectNotRegisteredError) as excinfo:
        await person.a_add_alias("test_add_alias_to_non_persitent_object_async")
    assert "is not registered!" in str(excinfo.value)
