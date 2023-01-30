import pytest
from model.family import Dog, Family, Person


def test_move_object(start_client):
    """Test a simple make_persistent call"""
    person = Person("Marc", 24)
    person.make_persistent()
    old_backend_id = person._dc_backend_id
    backend_ids = list(start_client.get_all_backends())
    backend_ids.remove(old_backend_id)

    person.move(backend_ids[0])
    assert person._dc_backend_id == backend_ids[0]
