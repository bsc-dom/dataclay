import pytest
from model.family import Dog, Family, Person


def test_move_object(client):
    """Test move to new backend"""
    person = Person("Marc", 24)
    person.make_persistent()

    current_backend_id = person._dc_backend_id
    backends = client.get_backends()
    backends.pop(current_backend_id)
    new_backend_id = list(backends)[0]

    person.move(new_backend_id)
    assert person._dc_backend_id == new_backend_id


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
