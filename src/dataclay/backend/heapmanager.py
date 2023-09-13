from __future__ import annotations

import gc
import logging
import pickle
import threading
from typing import TYPE_CHECKING

import psutil

from dataclay.config import settings
from dataclay.runtime import LockManager
from dataclay.utils import metrics
from dataclay.utils.serialization import DataClayPickler

if TYPE_CHECKING:
    from uuid import UUID

    from dataclay.dataclay_object import DataClayObject

# logger: logging.Logger = utils.LoggerEvent(logging.getLogger(__name__))
logger = logging.getLogger(__name__)


class HeapManager(threading.Thread):
    """This class is intended to manage all dataClay objects in runtime's memory."""

    def __init__(self):
        threading.Thread.__init__(self, name="heap-manager")

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

    #####

    def shutdown(self):
        """Stop this thread"""
        logger.debug("HEAP MANAGER shutdown request received.")
        self._finished.set()

    def run(self):
        """Overrides run function"""
        # gc_check_time_interval_seconds = settings.memmgmt_check_time_interval / 1000.0
        gc_check_time_interval_seconds = 10
        while True:
            # logger.debug("HEAP MANAGER THREAD is awake...")
            if self._finished.is_set():
                break
            self.run_task()

            # sleep for interval or until shutdown
            # logger.debug("HEAP MANAGER THREAD is going to sleep...")
            self._finished.wait(gc_check_time_interval_seconds)

        logger.debug("HEAP MANAGER THREAD Finished.")

    #####################################
    # BackendHeapManager specific methods
    #####################################

    def retain_in_heap(self, dc_obj: DataClayObject):
        """Add a new Hard reference to the object provided. All code in stubs/exec classes using objects in dataClay heap are
        using weak references. In order to avoid objects to be GC without a flush in DB, HeapManager has hard-references to
        them and is the only one able to release them. This function creates the hard-reference.
        """
        logger.debug(f"({dc_obj._dc_meta.id}) Retained in heap ")
        self.loaded_objects[dc_obj._dc_meta.id] = dc_obj

    def release_from_heap(self, dc_obj: DataClayObject):
        """Release hard reference to object provided.

        Without hard reference, the object can be Garbage collected
        """
        logger.debug("Releasing object with id %s from retained map. ", dc_obj._dc_meta.id)
        try:
            del self.loaded_objects[dc_obj._dc_meta.id]
        except KeyError as e:
            logger.warning("Object with id %s is not loaded.", dc_obj._dc_meta.id)

    def unload_object(self, object_id: UUID, timeout: str = 0, force: bool = False):
        instance = self.loaded_objects[object_id]

        if LockManager.acquire_write(object_id, timeout) or force:
            try:
                logger.warning(f"({object_id}) Unloading {instance.__class__.__name__} to storage")
                assert instance._dc_is_loaded

                # NOTE: We do not serialize internal attributes, since these are
                # obtained from etcd, or are stateless
                path = f"{settings.storage_path}/{object_id}"
                state = instance._dc_state
                DataClayPickler(open(path, "wb")).dump(state)
                metrics.dataclay_stored_objects.inc()

                # TODO: update etcd metadata (since is loaded has changed)
                # and store object in file system
                instance._clean_dc_properties()
                instance._dc_is_loaded = False
                del self.loaded_objects[object_id]
            finally:
                LockManager.release_write(object_id)

    def is_memory_under_pressure(self):
        """Check if memory is under pressure

        Memory management in Python involves a private heap containing all Python objects and data structures.
        The management of this private heap is ensured internally by the Python memory manager.
        The Python memory manager has different components which deal with various dynamic storage management aspects,
        like sharing, segmentation, preallocation or caching.

        Returns:
            TRUE if memory is under pressure. FALSE otherwise.
        """

        # return True
        return psutil.virtual_memory().percent > (settings.memmgmt_pressure_fraction * 100)

    def is_memory_at_ease(self):
        # return False
        return psutil.virtual_memory().percent < (settings.memmgmt_ease_fraction * 100)

    def run_task(self):
        if self.flush_all_lock.locked():
            logger.debug("Already flushing all objects")
            return

        # Enters if memory is under pressure and the lock is not locked
        if self.is_memory_under_pressure() and self.run_task_lock.acquire(blocking=False):
            try:
                loaded_objects_keys = list(self.loaded_objects)
                logger.debug(f"Num loaded objects before: {len(self.loaded_objects)}")

                while loaded_objects_keys:
                    object_id = loaded_objects_keys.pop()
                    self.unload_object(object_id, timeout=0, force=False)

                    # TODO: ¿Do we need to call every time gc.collect()?
                    gc.collect()

                    if self.is_memory_at_ease() or self.flush_all_lock.locked():
                        break
                else:
                    logger.warning("All objects cleaned, but memory is not at ease.")

                logger.debug(f"Num loaded objects after: {len(self.loaded_objects)}")
                del loaded_objects_keys
                gc.collect()

            finally:
                self.run_task_lock.release()

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

                # ?List used to create a copy and avoid it to grow?
                for object_id in list(self.loaded_objects):
                    self.unload_object(object_id, timeout=unload_timeout, force=force_unload)

                logger.debug(f"Num loaded objects not flushed: {len(self.loaded_objects)}")

            finally:
                self.flush_all_lock.release()

        else:
            logger.debug("Already flushing all objects")
