import pytest

from dataclay.contrib.modeltest.family import Person
from dataclay.exceptions import DataClayException


def test_get_by_alias(client):
    person = Person("Marc", 24)
    person.make_persistent(alias="test_get_by_alias")
    assert person is Person.get_by_alias("test_get_by_alias")
    Person.delete_alias("test_get_by_alias")


@pytest.mark.asyncio
async def test_get_by_alias_async(client):
    person = Person("Marc", 24)
    await person.a_make_persistent(alias="test_get_by_alias_async")
    assert person is await Person.a_get_by_alias("test_get_by_alias_async")
    await Person.a_delete_alias("test_get_by_alias_async")


def test_delete_alias(client):
    person = Person("Marc", 24)
    person.make_persistent("test_delete_alias")

    Person.delete_alias("test_delete_alias")
    with pytest.raises(DataClayException) as excinfo:
        Person.get_by_alias("test_delete_alias")
    assert "does not exist" in str(excinfo.value)


@pytest.mark.asyncio
async def test_delete_alias_async(client):
    person = Person("Marc", 24)
    await person.a_make_persistent("test_delete_alias_async")

    await Person.a_delete_alias("test_delete_alias_async")
    with pytest.raises(DataClayException) as excinfo:
        await Person.a_get_by_alias("test_delete_alias_async")
    assert "does not exist" in str(excinfo.value)


def test_same_alias(client):
    person_1 = Person("Marc", 24)
    person_2 = Person("Alice", 21)
    with pytest.raises(DataClayException) as excinfo:
        person_1.make_persistent("test_same_alias")
        person_2.make_persistent("test_same_alias")
    assert "already exist" in str(excinfo.value)
    Person.delete_alias("test_same_alias")


@pytest.mark.asyncio
async def test_same_alias_async(client):
    person_1 = Person("Marc", 24)
    person_2 = Person("Alice", 21)
    with pytest.raises(DataClayException) as excinfo:
        await person_1.a_make_persistent("test_same_alias_async")
        await person_2.a_make_persistent("test_same_alias_async")
    assert "already exist" in str(excinfo.value)
    await Person.a_delete_alias("test_same_alias")


def test_add_alias(client):
    person = Person("Marc", 24)
    person.make_persistent()
    person.add_alias("test_add_alias")
    assert person is Person.get_by_alias("test_add_alias")
    Person.delete_alias("test_add_alias")


@pytest.mark.asyncio
async def test_add_alias_async(client):
    person = Person("Marc", 24)
    await person.a_make_persistent()
    await person.a_add_alias("test_add_alias_async")
    assert person is await Person.a_get_by_alias("test_add_alias_async")
    await Person.a_delete_alias("test_add_alias_async")


def test_get_aliases(client):
    person = Person("Marc", 24)
    person.make_persistent("test_get_aliases")
    person.add_alias("test_get_aliases_1")
    person.add_alias("test_get_aliases_2")
    aliases = person.get_aliases()
    assert "test_get_aliases" in aliases
    assert "test_get_aliases_1" in aliases
    assert "test_get_aliases_2" in aliases
    Person.delete_alias("test_get_aliases")
    Person.delete_alias("test_get_aliases_1")
    Person.delete_alias("test_get_aliases_2")


@pytest.mark.asyncio
async def test_get_aliases_async(client):
    person = Person("Marc", 24)
    await person.a_make_persistent("test_get_aliases_async")
    await person.a_add_alias("test_get_aliases_1_async")
    await person.a_add_alias("test_get_aliases_2_async")
    aliases = await person.a_get_aliases()
    assert "test_get_aliases_async" in aliases
    assert "test_get_aliases_1_async" in aliases
    assert "test_get_aliases_2_async" in aliases
    await Person.a_delete_alias("test_get_aliases_async")
    await Person.a_delete_alias("test_get_aliases_1_async")
    await Person.a_delete_alias("test_get_aliases_2_async")
