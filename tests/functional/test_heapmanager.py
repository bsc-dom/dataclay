from dataclay.contrib.modeltest.family import Dog, Family, Person
from dataclay.event_loop import run_dc_coroutine


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


def test_unloaded_get_property(client):
    backends = client.get_backends()
    backend_ids = list(backends)

    person = Person("Marc", 24)
    person.make_persistent(backend_id=backend_ids[0])

    run_dc_coroutine(backends[backend_ids[0]].flush_all)
    assert person.name == "Marc"


def test_unloaded_set_property(client):
    backends = client.get_backends()
    backend_ids = list(backends)

    person = Person("Marc", 24)
    person.make_persistent(backend_id=backend_ids[0])

    run_dc_coroutine(backends[backend_ids[0]].flush_all)
    person.name = "Alice"
    assert person.name == "Alice"


def test_load_from_inmemory(client):
    backends = client.get_backends()
    backend_ids = list(backends)

    person = Person("Marc", 24)
    family = Family(person)
    family.make_persistent(backend_id=backend_ids[0])

    # call to flush_all to unload all objects
    run_dc_coroutine(backends[backend_ids[0]].flush_all)
    person.name = "Alice"

    assert family.members[0].name == "Alice"
