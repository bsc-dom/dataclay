import pytest

import storage.api
from dataclay.contrib.modeltest.family import Family, Person
from dataclay.event_loop import run_dc_coroutine


def test_new_version_and_consolidate(client):
    person = Person("Marc", 24)
    person.make_persistent()

    person_v1 = person.new_version()
    person_v1.name = "Alice"
    assert person.name == "Marc"

    person_v1.consolidate_version()
    assert person.name == "Alice"


@pytest.mark.asyncio
async def test_new_version_and_consolidate_async(client):
    person = Person("Marc", 24)
    await person.a_make_persistent()

    person_v1 = await person.a_new_version()
    person_v1.name = "Alice"
    assert person.name == "Marc"

    await person_v1.a_consolidate_version()
    assert person.name == "Alice"


def test_version_of_version(client):
    person = Person("Marc", 24)
    person.make_persistent()

    person_v1 = person.new_version()
    person_v1.name = "Alice"
    assert person.name == "Marc"

    person_v2 = person_v1.new_version()
    person_v2.name = "Carol"
    assert person_v1.name == "Alice"

    person_v2.consolidate_version()
    assert person.name == "Carol"


@pytest.mark.asyncio
async def test_version_of_version_async(client):
    person = Person("Marc", 24)
    await person.a_make_persistent()

    person_v1 = await person.a_new_version()
    person_v1.name = "Alice"
    assert person.name == "Marc"

    person_v2 = await person_v1.a_new_version()
    person_v2.name = "Carol"
    assert person_v1.name == "Alice"

    await person_v2.a_consolidate_version()
    assert person.name == "Carol"


def test_version_references(client):
    person = Person("Marc", 24)
    family = Family(person)
    person.make_persistent()

    person_v1 = person.new_version()
    person_v1.name = "Alice"
    assert person.name == "Marc"

    family_2 = Family(person_v1)

    person_v2 = person_v1.new_version()
    person_v2.name = "Carol"
    assert person_v1.name == "Alice"

    person_v2.consolidate_version()

    assert person.name == "Carol"
    assert family.members[0].name == "Carol"
    assert family_2.members[0].name == "Carol"


@pytest.mark.asyncio
async def test_version_references_async(client):
    person = Person("Marc", 24)
    family = Family(person)
    await person.a_make_persistent()

    person_v1 = await person.a_new_version()
    person_v1.name = "Alice"
    assert person.name == "Marc"

    family_2 = Family(person_v1)

    person_v2 = await person_v1.a_new_version()
    person_v2.name = "Carol"
    assert person_v1.name == "Alice"

    await person_v2.a_consolidate_version()

    assert person.name == "Carol"
    assert family.members[0].name == "Carol"
    assert family_2.members[0].name == "Carol"


def test_version_references_2(client):
    person = Person("Marc", 24)
    family = Family(person)
    family.make_persistent()

    person_v1 = person.new_version()
    person_v1.name = "Alice"
    assert person.name == "Marc"

    family_2 = Family()
    family_2.make_persistent()
    family_2.add(person_v1)

    person_v2 = person_v1.new_version()
    person_v2.name = "Carol"
    assert person_v1.name == "Alice"

    person_v2.consolidate_version()

    assert person.name == "Carol"
    assert family.members[0].name == "Carol"
    assert family_2.members[0].name == "Carol"


@pytest.mark.asyncio
async def test_version_references_2_async(client):
    person = Person("Marc", 24)
    family = Family(person)
    await family.a_make_persistent()

    person_v1 = await person.a_new_version()
    person_v1.name = "Alice"
    assert person.name == "Marc"

    family_2 = Family()
    await family_2.a_make_persistent()
    family_2.add(person_v1)

    person_v2 = await person_v1.a_new_version()
    person_v2.name = "Carol"
    assert person_v1.name == "Alice"

    await person_v2.a_consolidate_version()

    assert person.name == "Carol"
    assert family.members[0].name == "Carol"
    assert family_2.members[0].name == "Carol"


def test_version_references_3(client):
    person = Person("Marc", 24)
    family = Family(person)
    family.make_persistent()

    person_v1 = person.new_version()
    person_v1.name = "Alice"
    assert person.name == "Marc"

    family_2 = Family(person_v1)
    family_2.make_persistent()

    person_v2 = person_v1.new_version()
    person_v2.name = "Carol"
    assert person_v1.name == "Alice"

    person_v2.consolidate_version()

    assert person.name == "Carol"
    assert family.members[0].name == "Carol"
    assert family_2.members[0].name == "Carol"


@pytest.mark.asyncio
async def test_version_references_3_async(client):
    person = Person("Marc", 24)
    family = Family(person)
    await family.a_make_persistent()

    person_v1 = await person.a_new_version()
    person_v1.name = "Alice"
    assert person.name == "Marc"

    family_2 = Family(person_v1)
    await family_2.a_make_persistent()

    person_v2 = await person_v1.a_new_version()
    person_v2.name = "Carol"
    assert person_v1.name == "Alice"

    await person_v2.a_consolidate_version()

    assert person.name == "Carol"
    assert family.members[0].name == "Carol"
    assert family_2.members[0].name == "Carol"


def test_new_object_version(client):
    backends = client.get_backends()

    person = Person("Marc", 24)
    person.make_persistent()

    backend_client = backends[person._dc_meta.master_backend_id]
    person_v1_md_json = run_dc_coroutine(backend_client.new_object_version, person._dc_meta.id)
    person_v1 = storage.api.getByID(person_v1_md_json)

    assert person_v1.name == "Marc"

    person_v1.name = "Alice"
    assert person.name == "Marc"

    run_dc_coroutine(backend_client.consolidate_object_version, person_v1._dc_meta.id)
    assert person.name == "Alice"


@pytest.mark.asyncio
async def test_new_object_version_async(client):
    backends = await client.a_get_backends()

    person = Person("Marc", 24)
    await person.a_make_persistent()

    backend_client = backends[person._dc_meta.master_backend_id]
    person_v1_md_json = run_dc_coroutine(backend_client.new_object_version, person._dc_meta.id)
    person_v1 = storage.api.getByID(person_v1_md_json)

    assert person_v1.name == "Marc"

    person_v1.name = "Alice"
    assert person.name == "Marc"

    run_dc_coroutine(backend_client.consolidate_object_version, person_v1._dc_meta.id)
    assert person.name == "Alice"
