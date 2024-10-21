"""Module with classes for testing remote executions

Run `pytest -v -k "test_remote"` to run all remote executions
"""

from __future__ import annotations

from dataclay import DataClayObject, activemethod
from dataclay.config import get_runtime
from dataclay.contrib.modeltest.family import Person


class MakePersistentTestClass(DataClayObject):
    @activemethod
    def test_remote_automatic_register(self):
        """DataClay objects are persistent automatically in the backend"""
        person = Person("Marc", 24)
        assert person.is_persistent is True
        assert person.name == "Marc"
        assert person.age == 24
        assert person._dc_meta.master_backend_id == get_runtime().backend_id

        person.age = 55
        assert person.age == 55

    @activemethod
    def test_remote_make_persistent(self):
        """A call to make_persistent won't have any effect"""
        person = Person("Marc", 24)
        assert person.is_persistent is True
        person.make_persistent()
        assert person.is_persistent is True
        assert person.name == "Marc"
        assert person.age == 24
        assert person._dc_meta.master_backend_id == get_runtime().backend_id

    @activemethod
    def test_remote_make_persistent_alias(self):
        """A call to make_persistent with an alias will add the alias to the object"""
        person = Person("Marc", 24)
        assert person.is_persistent is True
        person.make_persistent()
        assert person.is_persistent is True

        person.make_persistent(alias="test_remote_make_persistent_alias")
        # person.sync()  # Sync to update object metadata
        assert "test_remote_make_persistent_alias" in person.get_aliases()

    @activemethod
    def test_remote_make_persistent_backend(self):
        """A call to make_persistent with a backend_id will move the object to the specified backend"""
        person = Person("Marc", 24)
        assert person.is_persistent is True
        person.make_persistent()
        assert person.is_persistent is True

        get_runtime().backend_clients.update()
        backend_ids = list(get_runtime().backend_clients)
        old_bid = person._dc_meta.master_backend_id
        if old_bid == backend_ids[0]:
            person.make_persistent(backend_id=backend_ids[1])
        else:
            person.make_persistent(backend_id=backend_ids[0])
        person.sync()  # Sync to update object metadata

        assert person._dc_meta.master_backend_id != old_bid


class ActivemethodTestClass(DataClayObject):
    @activemethod
    def test_activemethod(self):
        """DataClay objects can call activemethods"""
        person = Person("Marc", 24)
        assert person.age == 24

        person.add_year()
        assert person.age == 25


class MoveObjectTestClass(DataClayObject):
    @activemethod
    def test_move_object(self):
        person = Person("Marc", 24)
        # TODO: Should be awaited
        get_runtime().backend_clients.update()
        backend_ids = list(get_runtime().backend_clients)
        person.move(backend_ids[0])
        assert person._dc_meta.master_backend_id == backend_ids[0]
