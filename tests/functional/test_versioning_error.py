import pytest

from dataclay.contrib.modeltest.family import Person
from dataclay.exceptions import ObjectIsNotVersionError


def test_new_version_and_consolidate(client):
    person = Person("Marc", 24)
    person.make_persistent()
    with pytest.raises(ObjectIsNotVersionError) as excinfo:
        person.consolidate_version()
    assert "is not a version!" in str(excinfo.value)


@pytest.mark.asyncio
async def test_new_version_and_consolidate_async(client):
    person = Person("Marc", 24)
    await person.a_make_persistent()
    with pytest.raises(ObjectIsNotVersionError) as excinfo:
        await person.a_consolidate_version()
    assert "is not a version!" in str(excinfo.value)
