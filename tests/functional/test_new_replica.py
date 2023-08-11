import pytest

from dataclay.contrib.modeltest.family import Dog, Family, Person


def test_new_replica(client):
    """Test new replica"""
    person = Person("Marc", 24)
    person.make_persistent()

    assert len(person._dc_meta.replica_backend_ids) == 0
    person.new_replica()
    assert len(person._dc_meta.replica_backend_ids) == 1
    person.new_replica()
    person.new_replica()
    person.new_replica()
    person.new_replica()

    assert person._dc_meta.master_backend_id not in person._dc_meta.replica_backend_ids

    # assert person._dc_meta.master_backend_id == backend_ids[1]
