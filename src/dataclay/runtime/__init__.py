from contextlib import AbstractContextManager
from threading import Condition
from typing import TYPE_CHECKING

from dataclay.runtime.settings_hub import settings, unload_settings

if TYPE_CHECKING:
    from dataclay.runtime.client_runtime import ClientRuntime
    from dataclay.runtime.execution_environment_runtime import ExecutionEnvironmentRuntime

current_runtime = None


def get_runtime() -> "ClientRuntime | ExecutionEnvironmentRuntime":
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
