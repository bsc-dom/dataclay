"""Module with classes for testing remote executions

Run `pytest -v -k "test_remote"` to run all remote executions
"""

from __future__ import annotations

from threading import Thread

from dataclay import DataClayObject, activemethod
from dataclay.contrib.modeltest.family import Dog, Family, Person
from dataclay.runtime import get_runtime


class TestMakePersistent(DataClayObject):
    @activemethod
    def test_make_persistent(self):
        """DataClay objects are persistent automatically in the backend"""
        person = Person("Marc", 24)
        assert person.is_persistent == True
        assert person.name == "Marc"
        assert person.age == 24
        assert person._dc_meta.master_backend_id == get_runtime().backend_id

        person.age = 55
        assert person.age == 55


class TestActivemethod(DataClayObject):
    @activemethod
    def test_activemethod(self):
        """DataClay objects can call activemethods"""
        person = Person("Marc", 24)
        assert person.age == 24

        person.add_year()
        assert person.age == 25


class TestMoveObject(DataClayObject):
    @activemethod
    def test_move_object(self):
        from dataclay.runtime import get_runtime

        person = Person("Marc", 24)
        get_runtime().backend_clients.update()
        backend_ids = list(get_runtime().backend_clients)
        person.move(backend_ids[0])
        assert person._dc_meta.master_backend_id == backend_ids[0]
