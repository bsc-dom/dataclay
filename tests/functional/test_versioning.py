import pytest

from dataclay.contrib.modeltest.family import Dog, Family, Person


def test_new_version_and_consolidate(client):
    person = Person("Marc", 24)
    person.make_persistent()

    person_v1 = person.new_version()
    person_v1.name = "Alice"
    assert person.name == "Marc"

    person_v1.consolidate_version()
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


def test_new_object_version(client):
    backends = client.get_backends()
    backend_ids = list(backends)

    person = Person("Marc", 24)
    person.make_persistent()

    backend_client = backends[person._dc_backend_id]
    person_v1_info = backend_client.new_object_version(person._dc_id)
    person_v1_id, _, _ = person_v1_info.split(":")

    person_v1 = Person.get_by_id(person_v1_id)
    assert person_v1.name == "Marc"

    person_v1.name = "Alice"
    assert person.name == "Marc"

    backend_client.consolidate_object_version(person_v1._dc_id)
    assert person.name == "Alice"
