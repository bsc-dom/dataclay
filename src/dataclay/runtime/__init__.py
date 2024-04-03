from __future__ import annotations

import contextvars
import threading
from contextlib import contextmanager
from typing import TYPE_CHECKING, Union
from uuid import UUID

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop

    from dataclay.runtime.backend import BackendRuntime
    from dataclay.runtime.client import ClientRuntime


# Use for context-local data (current session, etc.)
session_var = contextvars.ContextVar("session")

current_runtime: Union[ClientRuntime, BackendRuntime, None] = None

dc_event_loop: AbstractEventLoop = None


def get_runtime() -> Union[ClientRuntime, BackendRuntime, None]:
    return current_runtime


def set_runtime(new_runtime: Union[ClientRuntime, BackendRuntime]):
    global current_runtime
    current_runtime = new_runtime


def set_dc_event_loop(loop):
    global dc_event_loop
    dc_event_loop = loop


def get_dc_event_loop() -> Union[None, AbstractEventLoop]:
    return dc_event_loop


class ReadWriteLock:
    """
    This class implements a read-write lock for objects identified by an object_id.

    The lock is reentrant for the same thread. Therefore, many read and write locks
    can be acquired by the same thread.

    The lock is not reentrant for different threads. Therefore, a thread cannot acquire
    a read lock if another thread has acquired a write lock, and viceversa.

    Many threads can acquire a read lock at the same time, but only one thread can acquire
    a write lock at the same time.
    """

    def __init__(self):
        self._write_lock = threading.RLock()
        self._cv = threading.Condition()
        self._read_count = 0
        self._local = threading.local()

    def acquire_read(self, timeout: float = None) -> bool:
        with self._cv:
            if self._cv.wait_for(lambda: self._write_lock.acquire(blocking=False), timeout):
                self._read_count += 1
                if not hasattr(self._local, "count"):
                    self._local.count = 0
                self._local.count += 1
                self._write_lock.release()
                self._cv.notify_all()
                return True
            else:
                return False

    def release_read(self):
        with self._cv:
            self._read_count -= 1
            self._local.count -= 1
            self._cv.notify_all()

    def acquire_write(self, timeout: float = None) -> bool:
        with self._cv:
            if not hasattr(self._local, "count"):
                self._local.count = 0
            return self._cv.wait_for(
                lambda: self._read_count == self._local.count
                and self._write_lock.acquire(blocking=False),
                timeout,
            )

    def release_write(self):
        with self._cv:
            self._write_lock.release()
            self._cv.notify_all()


class LockManager:
    """
    This class implements a global read-write lock manager for objects identified by an object_id.
    """

    object_locks: dict[UUID, ReadWriteLock] = {}
    class_lock = threading.Lock()

    @classmethod
    def acquire_read(cls, object_id, timeout=None):
        try:
            return cls.object_locks[object_id].acquire_read(timeout)
        except KeyError:
            with cls.class_lock:
                if object_id not in cls.object_locks:
                    cls.object_locks[object_id] = ReadWriteLock()
                return cls.object_locks[object_id].acquire_read(timeout)

    @classmethod
    def release_read(cls, object_id):
        cls.object_locks[object_id].release_read()

    @classmethod
    @contextmanager
    def read(cls, object_id):
        try:
            yield cls.acquire_read(object_id)
        finally:
            cls.release_read(object_id)

    @classmethod
    def acquire_write(cls, object_id, timeout=None):
        try:
            return cls.object_locks[object_id].acquire_write(timeout)
        except KeyError:
            with cls.class_lock:
                if object_id not in cls.object_locks:
                    cls.object_locks[object_id] = ReadWriteLock()
                return cls.object_locks[object_id].acquire_write(timeout)

    @classmethod
    def release_write(cls, object_id):
        cls.object_locks[object_id].release_write()

    @classmethod
    @contextmanager
    def write(cls, object_id):
        try:
            yield cls.acquire_write(object_id)
        finally:
            cls.release_write(object_id)
