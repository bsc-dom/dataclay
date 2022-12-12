import gc
import logging
import pickle
import threading
from typing import TYPE_CHECKING

import psutil

from dataclay.conf import settings
from dataclay.runtime import UUIDLock

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
        # Also, remember list must be thread-safe:
        self.loaded_objects: dict[UUID, DataClayObject] = dict()

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
        # gc_check_time_interval_seconds = settings.MEMMGMT_CHECK_TIME_INTERVAL / 1000.0
        gc_check_time_interval_seconds = 10
        while True:
            logger.debug("HEAP MANAGER THREAD is awake...")
            if self._finished.is_set():
                break
            self.run_task()

            # sleep for interval or until shutdown
            logger.debug("HEAP MANAGER THREAD is going to sleep...")
            self._finished.wait(gc_check_time_interval_seconds)

        logger.debug("HEAP MANAGER THREAD Finished.")

    #####################################
    # BackendHeapManager specific methods
    #####################################

    def retain_in_heap(self, dc_obj):
        """Add a new Hard reference to the object provided. All code in stubs/exec classes using objects in dataClay heap are
        using weak references. In order to avoid objects to be GC without a flush in DB, HeapManager has hard-references to
        them and is the only one able to release them. This function creates the hard-reference.
        """
        logger.debug("New object retained in heap")
        self.loaded_objects[dc_obj._dc_id] = dc_obj

    def release_from_heap(self, dc_obj):
        """Release hard reference to object provided.

        Without hard reference, the object can be Garbage collected
        """
        logger.debug("Releasing object with id %s from retained map. ", dc_obj._dc_id)
        try:
            del self.loaded_objects[dc_obj._dc_id]
        except Exception as e:
            logger.debug("Releasing object with id %s ", dc_obj._dc_id)

    def unload_object(self, object_id):

        instance = self.loaded_objects[object_id]

        xxx = instance._xdci_active_counter.acquire(timeout=0)
        print("XXXXXXXXXXXX", xxx)
        if xxx:
            try:
                with UUIDLock(object_id):

                    logger.warning(f"Storing and unloading object {object_id}")
                    assert instance._dc_is_loaded

                    # NOTE: We do not serialize internal attributes, since these are
                    # obtained from etcd, or are stateless
                    path = f"{settings.STORAGE_PATH}/{object_id}"
                    pickle.dump(instance._dc_properties, open(path, "wb"))

                    # TODO: update etcd metadata (since is loaded has changed)
                    # and store object in file system
                    instance.clean_dc_properties()
                    instance._dc_is_loaded = False

                    del self.loaded_objects[object_id]
            finally:
                instance._xdci_active_counter.release()

    def is_memory_under_pressure(self):
        """Check if memory is under pressure

        Memory management in Python involves a private heap containing all Python objects and data structures.
        The management of this private heap is ensured internally by the Python memory manager.
        The Python memory manager has different components which deal with various dynamic storage management aspects,
        like sharing, segmentation, preallocation or caching.

        Returns:
            TRUE if memory is under pressure. FALSE otherwise.
        """

        return True
        return psutil.virtual_memory().percent > (settings.MEMMGMT_PRESSURE_FRACTION * 100)

    def is_memory_at_ease(self):
        return False
        return psutil.virtual_memory().percent < (settings.MEMMGMT_EASE_FRACTION * 100)

    def run_task(self):

        if self.flush_all_lock.locked():
            logger.debug("Already running flush_all")
            return

        # Enters if memory is under pressure and the lock is not locked
        if self.is_memory_under_pressure() and self.run_task_lock.acquire(blocking=False):
            try:
                loaded_objects_keys = list(self.loaded_objects)
                logger.debug(f"Num loaded objects before: {len(loaded_objects_keys)}")

                while loaded_objects_keys:

                    object_id = loaded_objects_keys.pop()
                    self.unload_object(object_id)

                    # TODO: ¿Do we need to call every time gc.collect()?
                    gc.collect()

                    if self.is_memory_at_ease() or self.flush_all_lock.locked():
                        break
                else:
                    logger.warning("All objects cleaned, but still system memory pressure.")

                logger.debug(f"Num loaded objects after: {len(self.loaded_objects)}")
                del loaded_objects_keys
                gc.collect()

            finally:
                self.run_task_lock.release()

    def flush_all(self):
        """Stores all objects in memory into disk.

        This function is usually called at shutdown of the backend.
        """

        if self.flush_all_lock.acquire(blocking=False):

            try:
                logger.debug("Flushing all loaded objects")

                if self.run_task_lock.acquire(timeout=self.MAX_TIME_WAIT_FOR_GC_TO_FINISH):
                    self.run_task_lock.release()

                for object_id in list(self.loaded_objects):
                    self.unload_object(object_id)
            finally:
                self.flush_all_lock.release()

        else:
            logger.debug("Already running flush_all")
