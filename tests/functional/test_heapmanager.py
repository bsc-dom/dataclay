import pytest

from dataclay.contrib.modeltest.family import Dog, Family, Person


def test_self_is_not_unloaded(client):
    """Test a simple make_persistent call"""
    family = Family()
    family.make_persistent()
    family.test_self_is_not_unloaded()


def test_reference_is_unloaded(client):
    """Test a simple make_persistent call"""
    family = Family()
    family.make_persistent()
    family.test_reference_is_unloaded()


def test_load_from_inmemory(client):
    backends = client.get_backends()
    backend_ids = list(backends)

    person = Person("Marc", 24)
    family = Family(person)
    family.make_persistent(backend_id=backend_ids[0])

    # call to flush_all to unload all objects
    backends[backend_ids[0]].flush_all()
    person.name = "Alice"

    assert family.members[0].name == "Alice"
