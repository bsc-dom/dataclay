import gc
import logging
import threading
import time
import traceback
from weakref import WeakValueDictionary

from dataclay import utils

try:
    import tracemalloc
except ImportError:
    tracemalloc = None

from typing import TYPE_CHECKING

import psutil

from dataclay import utils
from dataclay.conf import settings
from dataclay.dataclay_object import DC_PROPERTY_PREFIX
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
        self.TIME_WAIT_FOR_GC_TO_FINISH = 1
        self.MAX_TIME_WAIT_FOR_GC_TO_FINISH = 60

        # Retained objects so they cannot be GC by PythonGC.
        # It is very important to be a sorted list, so first elements to arrive are cleaned before,
        # n any deserialization from DB or parameter, objects deserialized first are referrers to
        # objects deserialized later. Second ones cannot be GC if first ones are not cleaned.
        # During GC,we should know that somehow. It's a hint but improves GC a lot.
        # Also, remember list must be thread-safe:
        # Lists themselves are thread-safe. In CPython the GIL protects against concurrent accesses to them
        self.retained_objects = list()

        # Store also the ObjectID, because it is the fastest way to check if a certain object
        # is there (we cannot rely on __eq__ operations on user-defined classes.
        self.retained_objects_id = set()

        # Loaded objects so they cannot be GC by PythonGC.
        # It is very important to be a sorted dict (guaranteed in py3.7), so first elements to arrive are cleaned before,
        # n any deserialization from DB or parameter, objects deserialized first are referrers to
        # objects deserialized later. Second ones cannot be GC if first ones are not cleaned.
        # During GC,we should know that somehow. It's a hint but improves GC a lot.
        # Also, remember list must be thread-safe:
        self.loaded_objects: dict[UUID, DataClayObject] = dict()

        # Indicates if HeapManager is flushing all objects in Heap to disk.
        self.is_flushing_all = False

        # Indicates if HeapManager is processing GC
        self.is_processing_gc = False

    ##############
    # Dict methods
    ##############

    # def __getitem__(self, object_id):
    #     return self.inmemory_objects[object_id]

    # def __setitem__(self, object_id, obj):
    #     self.inmemory_objects[object_id] = obj

    # def __contains__(self, item):
    #     return item in self.inmemory_objects

    # def __len__(self):
    #     return len(self.inmemory_objects)

    # def __delitem__(self, object_id):
    #     """Remove reference from Heap.

    #     Even if we remove it from the heap the object won't be Garbage collected
    #     untill HeapManager flushes the object and releases it.
    #     """
    #     # self.inmemory_objects.pop(object_id) # Maybe this?
    #     del self.inmemory_objects[object_id]

    # def keys(self):
    #     return self.inmemory_objects.keys()

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
            self.new_run_task()

            # sleep for interval or until shutdown
            logger.debug("HEAP MANAGER THREAD is going to sleep...")
            self._finished.wait(gc_check_time_interval_seconds)

        logger.debug("HEAP MANAGER THREAD Finished.")

    def count_loaded_objs(self):
        num_loaded_objs = 0
        for obj in self.inmemory_objects.values():
            if obj._dc_is_loaded:
                num_loaded_objs = num_loaded_objs + 1
        return num_loaded_objs

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

    def __check_memory_pressure(self):
        """Check if memory is under pressure

        Memory management in Python involves a private heap containing all Python objects and data structures.
        The management of this private heap is ensured internally by the Python memory manager.
        The Python memory manager has different components which deal with various dynamic storage management aspects,
        like sharing, segmentation, preallocation or caching.

        Returns:
            TRUE if memory is under pressure. FALSE otherwise.
        """
        virtual_mem = psutil.virtual_memory()
        mem_pressure_limit = settings.MEMMGMT_PRESSURE_FRACTION * 100
        logger.debug("Memory: %s", virtual_mem)
        logger.debug(f"Checking if Memory: {float(virtual_mem.percent)} > {mem_pressure_limit}")
        return False
        return float(virtual_mem.percent) > mem_pressure_limit

    def __check_memory_ease(self):
        """Check if memory is at ease

        Returns:
            TRUE if memory is at ease. FALSE otherwise.
        """
        # See __check_memory_pressure, as this is quite similar
        virtual_mem = psutil.virtual_memory()
        logger.trace("Memory: %s", virtual_mem)
        return False
        return float(virtual_mem.percent) < (settings.MEMMGMT_EASE_FRACTION * 100)

    def gc_collect_internal(self, object_to_update):
        """Update object in db or store it if volatile"""
        raise ("To refactor")
        try:
            logger.debug(f"Updating object {object_to_update._dc_id}")
            # Call EE update
            if object_to_update._dc_is_pending_to_register:
                logger.debug(f"Storing and registering object {object_to_update._dc_id}")
                obj_bytes = SerializationLibUtilsSingleton.serialize_for_db_gc(
                    object_to_update, False, None
                )
                self.exec_env.register_and_store_pending(object_to_update, obj_bytes, True)
            else:
                # TODO: use dirty flag to avoid trips to SL? how to update SL graph of references?
                logger.debug(f"Updating dirty object {object_to_update._dc_id}")
                obj_bytes = SerializationLibUtilsSingleton.serialize_for_db_gc(
                    object_to_update, False, None
                )
                self.runtime.update_to_sl(object_to_update._dc_id, obj_bytes, True)

        except:
            # do nothing
            traceback.print_exc()
        # TODO: set dataset for GC if set by user

    def is_memory_under_pressure(self):
        return True
        return psutil.virtual_memory().percent > 80

    def new_run_task(self):

        if self.is_memory_under_pressure():
            loaded_objects_copy = self.loaded_objects.copy()
            logger.debug(f"Num loaded objects before: {len(loaded_objects_copy)}")

            while loaded_objects_copy:

                object_id, instance = loaded_objects_copy.popitem()

                with UUIDLock(object_id):
                    if not instance._dc_is_loaded:
                        del self.loaded_objects[object_id]
                        return

                    instance._dc_is_loaded = False

                    # TODO: update etcd metadata (since is loaded has changed)
                    # and store object in file system
                    import pickle

                    path = f"{settings.STORAGE_PATH}/{object_id}"

                    # NOTE: We do not serialize internal attributes, since these are
                    # obtained from etcd, or are stateless
                    pickle.dump(instance._dc_properties, open(path, "wb"))

                    # Remove property attributes
                    instance.clean_dc_properties()

                    del self.loaded_objects[object_id]

                del instance

                # TODO: ¿Do we need to call every time gc.collect()?
                gc.collect()

                if not self.is_memory_under_pressure():
                    break
            else:
                logger.warning("All objects cleaned, but still system memory pressure.")

            logger.debug(f"Num loaded objects after: {len(loaded_objects_copy)}")
            del loaded_objects_copy
            gc.collect()

    def run_task(self):
        """Check Python VM's memory pressure and clean if necessary. Cleaning means flushing objects, setting
        all fields to none (to allow GC to work better) and remove from retained references. If volatile or pending to register,
        we remove it once registered.
        """
        if self.is_flushing_all or self.is_processing_gc:
            logger.debug("[==GC==] Not running since is being processed or flush all is being done")
            return

        # No race condition possible here since there is a time interval for run_gc that MUST be > than time spend to check
        # flag and set to True. Should we do it atomically?
        self.is_processing_gc = True
        try:
            logger.debug("[==GC==] Running GC")

            if self.__check_memory_pressure():
                logger.debug("System memory is under pressure, proceeding to clean up objects")

                # if (
                #     logger.isEnabledFor(logging.DEBUG)
                #     and tracemalloc is not None
                #     and tracemalloc.is_tracing()
                # ):
                #     logger.debug("Doing a snapshot...")
                #     snapshot = tracemalloc.take_snapshot()
                #     top_stats = snapshot.statistics("lineno")

                #     print("[ Top 10 ]")
                #     for stat in top_stats[:10]:
                #         print(stat)

                # TODO: Add some logs

                # Copy the references in order to process it in a plain fashion
                loaded_objects_copy = self.loaded_objects.copy()
                logger.debug(
                    "Starting iteration with #%d retained objects", len(self.retained_objects)
                )

                while loaded_objects_copy:
                    # We iterate through while-pop to ensure that the reference is freed
                    object_id, dc_obj = loaded_objects_copy.popitem()

                    # NOTE: Memory pinned is never set or used
                    # if dc_obj.get_memory_pinned():
                    #     logger.trace(
                    #         "Object %s is memory pinned, ignoring it", dc_obj._dc_id
                    #     )
                    #     continue

                    # if dc_obj._dc_id in self.runtime.volatiles_under_deserialization:
                    #     logger.trace("[==GC==] Not collecting since it is under deserialization.")
                    #     continue

                    self.__clean_object(dc_obj)
                    del dc_obj  # Remove reference from Frame

                    # Big heaps
                    # n = gc.collect()
                    # if logger.isEnabledFor(logging.DEBUG) or logger.isEnabledFor(logging.TRACE):
                    #     if n > 0:
                    #         logger.debug("[==GC==] Collected %d", n)
                    #     else:
                    #         logger.trace("[==GC==] No objects collected")
                    #     if gc.garbage:
                    #         logger.debug("[==GC==] Uncollectable: %s", gc.garbage)
                    #     else:
                    #         logger.trace("[==GC==] No uncollectable objects")

                    # Check memory
                    at_ease = self.__check_memory_ease()
                    if at_ease:
                        logger.debug("Not collecting since memory is 'at ease' now")
                        break
                    if self.is_flushing_all:
                        logger.debug("Interrupted due to flush all.")
                        break
                else:
                    # This block is only entered when the while has finished (with no break statement)
                    # which means that all the objects have been iterated
                    logger.warning(
                        "I did my best and ended up cleaning all retained_objects. This typically means"
                        " that there is a huge global memory pressure. Problematic."
                    )
                logger.debug(
                    "Finishing iteration with #%d retained objects", len(self.loaded_objects)
                )

                # For cyclic references
                # n = gc.collect()

                # if logger.isEnabledFor(logging.DEBUG) or logger.isEnabledFor(logging.TRACE):
                #     if loaded_objects_copy:
                #         logger.debug(
                #             "There are #%d remaining objects after Garbage Collection",
                #             len(loaded_objects_copy),
                #         )
                #     if n > 0:
                #         logger.debug("[==GC==] Finally Collected %d", n)
                #     else:
                #         logger.trace("[==GC==] No objects collected")
                #     if gc.garbage:
                #         logger.debug("[==GC==] Uncollectable: %s", gc.garbage)
                #     else:
                #         logger.trace("[==GC==] No uncollectable objects")

                del loaded_objects_copy

                # if (
                #     logger.isEnabledFor(logging.DEBUG)
                #     and tracemalloc is not None
                #     and tracemalloc.is_tracing()
                # ):
                #     logger.debug("Doing a snapshot...")
                #     snapshot2 = tracemalloc.take_snapshot()

                #     top_stats = snapshot2.compare_to(snapshot, "lineno")

                #     print("[ Top 10 differences ]")
                #     for stat in top_stats[:10]:
                #         print(stat)
        except:
            # TODO: Interrupted thread for some reason (sigkill?). Make sure to flag is_processing_gc to false.
            pass
        self.is_processing_gc = False
        return

    def flush_all(self):
        """Stores all objects in memory into disk.

        This function is usually called at shutdown of the execution environment.
        """
        # If there is another flush, return
        if self.is_flushing_all:
            return

        self.is_flushing_all = True

        # If there is GC being processed, wait
        max_wait_time = 0
        while self.is_processing_gc and max_wait_time < self.MAX_TIME_WAIT_FOR_GC_TO_FINISH:
            logger.debug("[==FlushAll==] Waiting for GC to finish...")
            time.sleep(self.TIME_WAIT_FOR_GC_TO_FINISH)
            max_wait_time = max_wait_time + self.TIME_WAIT_FOR_GC_TO_FINISH

        logger.debug("[==FlushAll==] Number of objects in Heap: %s", len(self))
        for object_to_update in self.retained_objects:
            self.gc_collect_internal(object_to_update)

        return
