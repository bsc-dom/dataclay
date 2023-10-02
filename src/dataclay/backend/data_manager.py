from __future__ import annotations

import gc
import logging
import pickle
import threading
from typing import TYPE_CHECKING

import psutil

from dataclay.config import settings
from dataclay.exceptions import *
from dataclay.runtime import LockManager
from dataclay.utils import metrics
from dataclay.utils.serialization import DataClayPickler

if TYPE_CHECKING:
    from uuid import UUID

    from dataclay.dataclay_object import DataClayObject

# logger: logging.Logger = utils.LoggerEvent(logging.getLogger(__name__))
logger = logging.getLogger(__name__)


class DataManager(threading.Thread):
    """This class is intended to manage all dataClay objects in runtime's memory."""

    def __init__(self):
        threading.Thread.__init__(self, name="data-manager")

        # Event object to communicate shutdown
        self._finished = threading.Event()

        self.daemon = True

        # During a flush of all objects in Heap, if GC is being processed, wait, and check after time specified here in seconds
        self.MAX_TIME_WAIT_FOR_GC_TO_FINISH = 60

        # Loaded objects so they cannot be GC by PythonGC.
        # It is very important to be a sorted dict (guaranteed in py3.7), so first elements to arrive are cleaned before,
        # n any deserialization from DB or parameter, objects deserialized first are referrers to
        # objects deserialized later. Second ones cannot be GC if first ones are not cleaned.
        # During GC,we should know that somehow. It's a hint but improves GC a lot.
        self.loaded_objects: dict[UUID, DataClayObject] = {}
        metrics.dataclay_loaded_objects.set_function(lambda: len(self.loaded_objects))

        # Locks for run_task and flush_all
        self.run_task_lock = threading.Lock()
        self.flush_all_lock = threading.Lock()

    def run(self):
        """Overrides run function"""
        gc_check_time_interval_seconds = settings.memory_check_interval
        while True:
            logger.debug("Thread is awake")
            if self._finished.is_set():
                break
            self.run_task()

            # sleep for interval or until shutdown
            logger.debug("Thread is going to sleep")
            self._finished.wait(gc_check_time_interval_seconds)

        logger.debug("Thread stoped")

    def run_task(self):
        if self.flush_all_lock.locked():
            logger.debug("Already flushing all objects")
            return

        # Enters if memory is over threshold and the lock is not locked
        if self.is_memory_over_threshold() and self.run_task_lock.acquire(blocking=False):
            try:
                logger.debug(f"Num loaded objects before: {len(self.loaded_objects)}")
                for object_id in list(self.loaded_objects.keys()):
                    self.unload_object(self.loaded_objects[object_id], timeout=0, force=False)

                    # TODO: ¿Do we need to call every time gc.collect()?
                    gc.collect()
                    if self.is_memory_at_ease() or self.flush_all_lock.locked():
                        break
                else:
                    logger.warning("All objects unloaded, but memory is not at ease.")

                logger.debug(f"Num loaded objects after: {len(self.loaded_objects)}")
            finally:
                self.run_task_lock.release()

    def add_hard_reference(self, instance: DataClayObject):
        """Add a hard reference to the provided object."""
        logger.debug(f"({instance._dc_meta.id}) Adding hard reference to heap")
        self.loaded_objects[instance._dc_meta.id] = instance

    def remove_hard_reference(self, instance: DataClayObject):
        """Remove the hard reference to the provided object."""
        logger.debug(f"({instance._dc_meta.id}) Removing hard reference from heap")
        self.loaded_objects.pop(instance._dc_meta.id, None)

    def load_object(self, instance: DataClayObject):
        object_id = instance._dc_meta.id

        with LockManager.write(object_id):
            if instance._dc_is_loaded or not instance._dc_is_local:
                # Object may had been loaded in another thread while waiting for lock
                logger.warning(f"({object_id}) Object already loaded or not local")
                return

            logger.debug(f"({object_id}) Loading {instance.__class__.__name__}")
            assert object_id not in self.loaded_objects

            try:
                path = f"{settings.storage_path}/{object_id}"
                object_dict, state = pickle.load(open(path, "rb"))
                metrics.dataclay_stored_objects.dec()
            except Exception as e:
                raise DataClayException("Object not found.") from e

            # The object_dict don't contain extradata (e.g. _dc_is_loaded)
            object_dict["_dc_is_loaded"] = True

            # Remove serialized metadata in case it is outdated. Already have it from Redis.
            del object_dict["_dc_meta"]
            vars(instance).update(object_dict)

            # If object has defined __getstate__ and __setstate__, call them
            if state:
                instance.__setstate__(state)
            self.add_hard_reference(instance)

    def unload_object(self, instance: DataClayObject, timeout: str = 0, force: bool = False):
        object_id = instance._dc_meta.id

        if LockManager.acquire_write(object_id, timeout) or force:
            try:
                logger.warning(f"({object_id}) Unloading {instance.__class__.__name__}")
                assert instance._dc_is_loaded
                assert object_id in self.loaded_objects

                # Not serializing metadata nor extradata. These are saved in redis
                path = f"{settings.storage_path}/{object_id}"
                state = instance._dc_state
                DataClayPickler(open(path, "wb")).dump(state)
                metrics.dataclay_stored_objects.inc()

                # TODO: Maybe update Redis (since is loaded has changed). For access optimization.
                instance._clean_dc_properties()
                instance._dc_is_loaded = False
                del self.loaded_objects[object_id]
            finally:
                LockManager.release_write(object_id)

    def is_memory_over_threshold(self):
        """Check if memory usage is over a specified threshold.

        Returns:
            True if memory usage exceeds the threshold, False otherwise.
        """
        return psutil.virtual_memory().percent > (settings.memory_threshold_high * 100)

    def is_memory_below_threshold(self):
        """Check if memory usage is below a specified threshold.

        Returns:
            True if memory usage is below the threshold, False otherwise.
        """
        return psutil.virtual_memory().percent < (settings.memory_threshold_low * 100)

    def flush_all(self, unload_timeout: str | None = None, force_unload: bool = True):
        """Stores and unloads all loaded objects to disk.

        This function is usually called at shutdown of the backend.
        """

        if unload_timeout is None:
            unload_timeout = settings.unload_timeout

        if self.flush_all_lock.acquire(blocking=False):
            try:
                logger.debug(
                    f"Starting to flush all loaded objects. Num ({len(self.loaded_objects)})"
                )

                if self.run_task_lock.acquire(timeout=self.MAX_TIME_WAIT_FOR_GC_TO_FINISH):
                    self.run_task_lock.release()

                for object_id in list(self.loaded_objects.keys()):
                    self.unload_object(
                        self.loaded_objects[object_id], timeout=unload_timeout, force=force_unload
                    )

                logger.debug(f"Num loaded objects not flushed: {len(self.loaded_objects)}")

            finally:
                self.flush_all_lock.release()

        else:
            logger.debug("Flushing already in progress...")

    def shutdown(self):
        """Stop this thread"""
        logger.debug("Shutdown request received")
        self._finished.set()
