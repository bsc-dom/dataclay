import pytest

from dataclay.contrib.modeltest.family import Dog, Family, Person
from dataclay.contrib.modeltest.test_remote import TestMoveObject


def test_move_object(client):
    """Test move to new backend"""
    backend_ids = list(client.get_backends())

    person = Person("Marc", 24)
    person.make_persistent(backend_id=backend_ids[0])

    person.move(backend_ids[1])
    assert person._dc_meta.master_backend_id == backend_ids[1]


def test_recursive_move(client):
    """When moving recursively an object to new backend, all references
    should also be moved (check gc)"""
    backend_ids = list(client.get_backends())

    person_1 = Person("Marc", 24)
    person_1.make_persistent(backend_id=backend_ids[0])
    person_2 = Person("Alice", 21)
    person_2.make_persistent(backend_id=backend_ids[1])
    family = Family(person_1, person_2)
    family.make_persistent(backend_id=backend_ids[0])
    family.move(backend_ids[2], recursive=True)

    # person_1 and person_2 should change
    person_1.sync()  # forcing update of backend_id
    assert person_1._dc_meta.master_backend_id == backend_ids[2]
    person_2.sync()  # forcing update of backend_id
    assert person_2._dc_meta.master_backend_id == backend_ids[2]


def test_not_recursive_move(client):
    """When moving an object (not recursively) to new backend, none reference
    should be moved"""
    backend_ids = list(client.get_backends())

    person = Person("Marc", 24)
    family = Family(person)
    family.make_persistent(backend_id=backend_ids[0])
    family.move(backend_ids[1])

    person.sync()  # forcing update of backend_id
    assert person._dc_meta.master_backend_id == backend_ids[0]


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
    assert person._dc_meta.master_backend_id == backend_ids[1]


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
    assert person._dc_meta.master_backend_id == backend_ids[0]

    # We set a wrong backend_id
    person._dc_meta.master_backend_id = backend_ids[1]
    assert person._dc_meta.master_backend_id == backend_ids[1]
    assert person.name == "Marc"
    assert person._dc_meta.master_backend_id == backend_ids[0]


def test_move_recursive_remotes(client):
    """The dc object and all its references, even remote references (in other backends),
    should be moved"""
    backend_ids = list(client.get_backends())

    person = Person("Marc", 24)
    person.make_persistent(backend_id=backend_ids[0])
    family = Family(person)
    family.make_persistent(backend_id=backend_ids[1])
    family.move(backend_ids[2], recursive=True)

    # person should change
    person.sync()  # forcing update of backend_id
    assert person._dc_meta.master_backend_id == backend_ids[2]


def test_move_recursive_not_remotes(client):
    """Only the dc object and the local references should be moved"""
    backend_ids = list(client.get_backends())

    person_1 = Person("Marc", 24)
    person_1.make_persistent(backend_id=backend_ids[0])
    person_2 = Person("Alice", 21)
    person_2.make_persistent(backend_id=backend_ids[1])

    family = Family(person_1, person_2)
    family.make_persistent(backend_id=backend_ids[0])
    family.move(backend_ids[2], recursive=True, remotes=False)

    # person_1 should change, but not person_2
    person_1.sync()  # forcing update of backend_id
    assert person_1._dc_meta.master_backend_id == backend_ids[2]
    person_2.sync()  # forcing update of backend_id
    assert person_2._dc_meta.master_backend_id == backend_ids[1]


def test_move_recursive_reference_of_reference_v1(client):
    """All the references should be recursively moved"""
    backend_ids = list(client.get_backends())

    person_1 = Person("Marc", 24)
    person_1.make_persistent(backend_id=backend_ids[0])
    person_2 = Person("Alice", 21)
    person_2.make_persistent(backend_id=backend_ids[0])
    person_3 = Person("Carol", 56)
    person_3.make_persistent(backend_id=backend_ids[1])
    person_4 = Person("Javi", 55)
    person_4.make_persistent(backend_id=backend_ids[1])

    person_1.spouse = person_2
    person_2.spouse = person_3
    person_3.spouse = person_4

    family = Family(person_1)
    family.make_persistent(backend_id=backend_ids[0])
    family.move(backend_ids[2], recursive=True)

    person_1.sync()  # forcing update of backend_id
    assert person_1._dc_meta.master_backend_id == backend_ids[2]
    person_2.sync()  # forcing update of backend_id
    assert person_2._dc_meta.master_backend_id == backend_ids[2]
    person_3.sync()  # forcing update of backend_id
    assert person_3._dc_meta.master_backend_id == backend_ids[2]
    person_4.sync()  # forcing update of backend_id
    assert person_4._dc_meta.master_backend_id == backend_ids[2]


def test_move_recursive_reference_of_reference_v2(client):
    """All the references should be recursively moved"""
    backend_ids = list(client.get_backends())

    person_1 = Person("Marc", 24)
    person_1.make_persistent(backend_id=backend_ids[0])
    person_2 = Person("Alice", 21)
    person_2.make_persistent(backend_id=backend_ids[0])
    person_3 = Person("Carol", 56)
    person_3.make_persistent(backend_id=backend_ids[1])
    person_4 = Person("Javi", 55)
    person_4.make_persistent(backend_id=backend_ids[2])

    person_1.spouse = person_2
    person_2.spouse = person_3
    person_3.spouse = person_4

    family = Family(person_1)
    family.make_persistent(backend_id=backend_ids[0])
    family.move(backend_ids[2], recursive=True)

    person_1.sync()  # forcing update of backend_id
    assert person_1._dc_meta.master_backend_id == backend_ids[2]
    person_2.sync()  # forcing update of backend_id
    assert person_2._dc_meta.master_backend_id == backend_ids[2]
    person_3.sync()  # forcing update of backend_id
    assert person_3._dc_meta.master_backend_id == backend_ids[2]
    person_4.sync()  # forcing update of backend_id
    assert person_4._dc_meta.master_backend_id == backend_ids[2]


def test_move_recursive_reference_of_reference_v3(client):
    """All the references should be recursively moved"""
    backend_ids = list(client.get_backends())

    person_1 = Person("Marc", 24)
    person_1.make_persistent(backend_id=backend_ids[2])
    person_2 = Person("Alice", 21)
    person_2.make_persistent(backend_id=backend_ids[2])
    person_3 = Person("Carol", 56)
    person_3.make_persistent(backend_id=backend_ids[1])
    person_4 = Person("Javi", 55)
    person_4.make_persistent(backend_id=backend_ids[0])

    person_1.spouse = person_2
    person_2.spouse = person_3
    person_3.spouse = person_4

    family = Family(person_1)
    family.make_persistent(backend_id=backend_ids[0])
    family.move(backend_ids[2], recursive=True)

    person_1.sync()  # forcing update of backend_id
    assert person_1._dc_meta.master_backend_id == backend_ids[2]
    person_2.sync()  # forcing update of backend_id
    assert person_2._dc_meta.master_backend_id == backend_ids[2]
    person_3.sync()  # forcing update of backend_id
    assert person_3._dc_meta.master_backend_id == backend_ids[2]
    person_4.sync()  # forcing update of backend_id
    assert person_4._dc_meta.master_backend_id == backend_ids[2]


def test_move_recursive_reference_of_reference_v4(client):
    """All the references should be recursively moved"""
    backend_ids = list(client.get_backends())

    person_1 = Person("Marc", 24)
    person_1.make_persistent(backend_id=backend_ids[0])
    person_2 = Person("Alice", 21)
    person_2.make_persistent(backend_id=backend_ids[0])
    person_3 = Person("Carol", 56)
    person_3.make_persistent(backend_id=backend_ids[1])
    person_4 = Person("Javi", 55)
    person_4.make_persistent(backend_id=backend_ids[2])

    person_1.spouse = person_2
    person_2.spouse = person_3
    person_3.spouse = person_4

    family = Family(person_1, person_2, person_3, person_4)
    family.make_persistent(backend_id=backend_ids[0])
    family.move(backend_ids[2], recursive=True)

    person_1.sync()  # forcing update of backend_id
    assert person_1._dc_meta.master_backend_id == backend_ids[2]
    person_2.sync()  # forcing update of backend_id
    assert person_2._dc_meta.master_backend_id == backend_ids[2]
    person_3.sync()  # forcing update of backend_id
    assert person_3._dc_meta.master_backend_id == backend_ids[2]
    person_4.sync()  # forcing update of backend_id
    assert person_4._dc_meta.master_backend_id == backend_ids[2]


def test_move_recursive_reference_cycle_v1(client):
    """All the references should be recursively moved"""
    backend_ids = list(client.get_backends())

    person_1 = Person("Marc", 24)
    person_1.make_persistent(backend_id=backend_ids[0])
    person_2 = Person("Alice", 21)
    person_2.make_persistent(backend_id=backend_ids[0])

    person_1.spouse = person_2
    person_2.spouse = person_1

    family = Family(person_1)
    family.make_persistent(backend_id=backend_ids[0])
    family.move(backend_ids[2], recursive=True)

    person_1.sync()  # forcing update of backend_id
    assert person_1._dc_meta.master_backend_id == backend_ids[2]
    person_2.sync()  # forcing update of backend_id
    assert person_2._dc_meta.master_backend_id == backend_ids[2]


def test_move_recursive_reference_cycle_v2(client):
    """All the references should be recursively moved"""
    backend_ids = list(client.get_backends())

    person_1 = Person("Marc", 24)
    person_1.make_persistent(backend_id=backend_ids[0])
    person_2 = Person("Alice", 21)
    person_2.make_persistent(backend_id=backend_ids[1])

    person_1.spouse = person_2
    person_2.spouse = person_1

    family = Family(person_1)
    family.make_persistent(backend_id=backend_ids[0])
    family.move(backend_ids[2], recursive=True)

    person_1.sync()  # forcing update of backend_id
    assert person_1._dc_meta.master_backend_id == backend_ids[2]
    person_2.sync()  # forcing update of backend_id
    assert person_2._dc_meta.master_backend_id == backend_ids[2]


def test_move_local_object(client):
    """If the object is already in the backend, it should not be moved,
    neither its references"""
    backend_ids = list(client.get_backends())

    person_1 = Person("Marc", 24)
    person_1.make_persistent(backend_id=backend_ids[0])
    person_2 = Person("Alice", 21)
    person_2.make_persistent(backend_id=backend_ids[1])

    family = Family(person_1, person_2)
    family.make_persistent(backend_id=backend_ids[0])
    family.move(backend_ids[0])

    person_1.sync()  # forcing update of backend_id
    assert person_1._dc_meta.master_backend_id == backend_ids[0]
    person_2.sync()  # forcing update of backend_id
    assert person_2._dc_meta.master_backend_id == backend_ids[1]


def test_move_local_object_recursive_remotes(client):
    """If the object is already in the backend, but recursive=True,
    and remotes=True, the remote references should be moved"""
    backend_ids = list(client.get_backends())

    person_1 = Person("Marc", 24)
    person_1.make_persistent(backend_id=backend_ids[0])
    person_2 = Person("Alice", 21)
    person_2.make_persistent(backend_id=backend_ids[1])
    person_3 = Person("Carol", 56)
    person_3.make_persistent(backend_id=backend_ids[1])
    person_4 = Person("Javi", 55)
    person_4.make_persistent(backend_id=backend_ids[2])

    person_1.spouse = person_2
    person_3.spouse = person_4

    family = Family(person_1, person_3)
    family.make_persistent(backend_id=backend_ids[0])
    family.move(backend_ids[0], recursive=True)

    person_1.sync()  # forcing update of backend_id
    assert person_1._dc_meta.master_backend_id == backend_ids[0]
    person_2.sync()  # forcing update of backend_id
    assert person_2._dc_meta.master_backend_id == backend_ids[0]
    person_3.sync()  # forcing update of backend_id
    assert person_3._dc_meta.master_backend_id == backend_ids[0]
    person_4.sync()  # forcing update of backend_id
    assert person_4._dc_meta.master_backend_id == backend_ids[0]


# Remote Methods


def test_remote_move_activemethod(client):
    """Move object inside an active method"""
    remote_test = TestMoveObject()
    remote_test.make_persistent()
    remote_test.test_move_object()
