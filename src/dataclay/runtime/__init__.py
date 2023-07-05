from contextlib import AbstractContextManager
from threading import Condition, Lock, RLock
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from dataclay.runtime.backend import BackendRuntime
    from dataclay.runtime.client import ClientRuntime

current_runtime = None


def get_runtime():
    return current_runtime


def set_runtime(new_runtime):
    global current_runtime
    current_runtime = new_runtime


class UUIDLock(AbstractContextManager):
    """This class is used as a global lock for UUIDs

    Use it always with context manager:
        with UUIDLock(id):
            ...
    """

    object_locks: dict[UUID, RLock] = dict()
    class_lock = Lock()

    def __init__(self, object_id):
        self.object_id = object_id

    def __enter__(self):
        try:
            self.object_locks[self.object_id].acquire()
            # NOTE: This assert checks that cleanup thread don't remove
            # lock while trying to acquire.
            assert self.object_id in self.object_locks
        except KeyError:
            with self.class_lock:
                try:
                    self.object_locks[self.object_id].acquire()
                except KeyError:
                    self.object_locks[self.object_id] = RLock()
                    self.object_locks[self.object_id].acquire()

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            self.object_locks[self.object_id].release()
        except KeyError:
            pass


# NOTE this lock is faster and don't require cleanup,
# however, it doesn't allow recursive locking in same thread
class UUIDLock_old(AbstractContextManager):
    """This class is used as a global lock for UUIDs

    Use it always with context manager:
        with UUIDLock(id):
            ...
    """

    cv = Condition()
    locked_objects = set()

    def __init__(self, id):
        self.id = id

    def __enter__(self):
        with self.cv:
            self.cv.wait_for(lambda: self.id not in self.locked_objects)
            self.locked_objects.add(self.id)

    def __exit__(self, exc_type, exc_value, traceback):
        with self.cv:
            self.locked_objects.remove(self.id)
            self.cv.notify_all()
