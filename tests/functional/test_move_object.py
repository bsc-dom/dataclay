import pytest

from dataclay.contrib.modeltest.family import Dog, Family, Person


def test_move_object(client):
    """Test move to new backend"""
    backend_ids = list(client.get_backends())

    person = Person("Marc", 24)
    person.make_persistent(backend_id=backend_ids[0])

    person.move(backend_ids[1])
    assert person._dc_backend_id == backend_ids[1]


def test_recursive_move(client):
    """When moving recursively an object to new backend, all local references
    from the same backend should also be moved (check gc)"""
    backend_ids = list(client.get_backends())

    person_1 = Person("Marc", 24)
    person_1.make_persistent(backend_id=backend_ids[0])
    person_2 = Person("Alice", 21)
    person_2.make_persistent(backend_id=backend_ids[1])
    family = Family(person_1, person_2)
    family.make_persistent(backend_id=backend_ids[0])
    family.move(backend_ids[2], recursive=True)

    # person_1 should change backend, but person_2 should stay the same
    person_1.name  # forcing update of backend_id
    assert person_1._dc_backend_id == backend_ids[2]
    person_2.name  # forcing update of backend_id
    assert person_2._dc_backend_id == backend_ids[1]


def test_not_recursive_move(client):
    """When moving an object (not recursively) to new backend, none reference
    should be moved"""
    backend_ids = list(client.get_backends())

    person = Person("Marc", 24)
    family = Family(person)
    family.make_persistent(backend_id=backend_ids[0])
    family.move(backend_ids[1])

    person.name  # forcing update of backend_id
    assert person._dc_backend_id == backend_ids[0]


def test_move_unload_object(client):
    """Local non-loaded objects should be moved correctly.
    First loaded, and then moved with all properties"""
    backends = client.get_backends()
    backend_ids = list(backends)

    person = Person("Marc", 24)
    family = Family(person)
    family.make_persistent(backend_id=backend_ids[0])

    # call to flush_all to unload all objects
    backends[backend_ids[0]].flush_all()
    family.move(backend_ids[1], recursive=True)

    assert person.name == "Marc"  # forcing update of backend_id
    assert person._dc_backend_id == backend_ids[1]


def test_move_reference(client):
    """When moving object to new backend, if that backend already
    has the object as remote object, make it local.
    """
    backend_ids = list(client.get_backends())

    person = Person("Marc", 24)
    person.make_persistent(backend_id=backend_ids[0])

    family = Family(person)
    family.make_persistent(backend_id=backend_ids[1])

    person.move(backend_ids[1])
    assert person == family.members[0]


def test_wrong_backend_id(client):
    """When a dc object in client has a wrong backend_id (if it was moved),
    it should be updated after first wrong call."""
    backend_ids = list(client.get_backends())

    person = Person("Marc", 24)
    person.make_persistent(backend_id=backend_ids[0])
    assert person._dc_backend_id == backend_ids[0]

    # We set a wrong backend_id
    person._dc_backend_id = backend_ids[1]
    assert person._dc_backend_id == backend_ids[1]
    assert person.name == "Marc"
    assert person._dc_backend_id == backend_ids[0]
