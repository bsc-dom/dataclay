""" Class description goes here. """

"""
Created on 26 ene. 2018

@author: dgasull
"""

import gc
import logging
import sys
import time
import traceback
from weakref import WeakValueDictionary

try:
    import tracemalloc
except ImportError:
    tracemalloc = None

import psutil
from dataclay.DataClayObjProperties import DCLAY_PROPERTY_PREFIX
from dataclay.heap.HeapManager import HeapManager
from dataclay.serialization.lib.DeserializationLibUtils import DeserializationLibUtilsSingleton
from dataclay.serialization.lib.SerializationLibUtils import SerializationLibUtilsSingleton
from dataclay.util import Configuration
from dataclay_common import utils

logger = utils.LoggerEvent(logging.getLogger(__name__))


class ExecutionEnvironmentHeapManager(HeapManager):
    def __init__(self, theruntime):
        super().__init__(theruntime)

        # During a flush of all objects in Heap, if GC is being processed, wait, and check after time specified here in seconds
        self.TIME_WAIT_FOR_GC_TO_FINISH = 1
        self.MAX_TIME_WAIT_FOR_GC_TO_FINISH = 60

        # Execution Environment being managed
        self.exec_env = theruntime.get_execution_environment()

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

        # Indicates if HeapManager is flushing all objects in Heap to disk.
        self.is_flushing_all = False

        # Indicates if HeapManager is processing GC
        self.is_processing_gc = False

        logger.debug("EE HEAP MANAGER created for EE %s", self.exec_env.ee_name)

    def get_object_ids_retained(self):
        """get ids of objects retained in memory"""
        logger.debug("Retained refs: %s " % str(len(self.retained_objects)))
        logger.debug("Inmemory refs: %s " % str(len(self.inmemory_objects)))
        return self.inmemory_objects.keys()

    def add_to_heap(self, dc_object):
        """the object is added to dataClay's heap"""
        self._add_to_inmemory_map(dc_object)
        self.retain_in_heap(dc_object)

    def retain_in_heap(self, dc_object):
        """Add a new Hard reference to the object provided. All code in stubs/exec classes using objects in dataClay heap are
        using weak references. In order to avoid objects to be GC without a flush in DB, HeapManager has hard-references to
        them and is the only one able to release them. This function creates the hard-reference.
        """
        if dc_object._object_id not in self.retained_objects_id:
            self.retained_objects_id.add(dc_object._object_id)
            self.retained_objects.append(dc_object)

    def release_from_heap(self, dc_obj):
        """Release hard reference to object provided.

        Without hard reference, the object can be Garbage collected
        """
        logger.debug("Releasing object with id %s from retained map. ", dc_obj._object_id)
        try:
            self.retained_objects_id.remove(dc_obj._object_id)
            self.retained_objects.remove(dc_obj)
        except Exception as e:
            logger.debug("Releasing object with id %s ", dc_obj._object_id)

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
        mem_pressure_limit = Configuration.MEMMGMT_PRESSURE_FRACTION * 100
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
        return float(virtual_mem.percent) < (Configuration.MEMMGMT_EASE_FRACTION * 100)

    def __nullify_object(self, dc_object):
        """Set all fields to none to allow GC action"""

        metaclass = dc_object.get_class_extradata()
        logger.debug("Going to clean object %s", dc_object._object_id)

        # Put here because it is critical path and I prefer to have a single isEnabledFor
        # instead of checking it for each element
        if logger.isEnabledFor(logging.DEBUG):
            held_objects = WeakValueDictionary()

            o = None
            prop_name_list = metaclass.properties.keys()

            logger.debug(
                "The following attributes will be nullified from object %s: %s",
                dc_object._object_id,
                ", ".join(prop_name_list),
            )

            for prop_name in prop_name_list:
                real_prop_name = "%s%s" % (DCLAY_PROPERTY_PREFIX, prop_name)

                try:
                    o = object.__getattribute__(dc_object, real_prop_name)
                    held_objects[prop_name] = o
                except TypeError:
                    # Some objects cannot be weakreferenced, but we can typically ignore them
                    logger.trace("Ignoring attribute %s of type %s", prop_name, type(o))

            # Ensure we don't keep that as a dangling active backref
            del o

        # Critical path, keep it short!
        for prop_name in metaclass.properties.keys():
            real_prop_name = "%s%s" % (DCLAY_PROPERTY_PREFIX, prop_name)
            object.__setattr__(dc_object, real_prop_name, None)

        if logger.isEnabledFor(logging.DEBUG):
            # held_objects variable will be defined when TRACE-enabled.
            held_attr_names = held_objects.keys()

            if held_attr_names:
                logger.debug(
                    "The following attributes of object %s still have a backref active: %s",
                    dc_object._object_id,
                    ", ".join(held_attr_names),
                )
            else:
                logger.debug(
                    "The garbage collector seems to have cleaned all the nullified attributes on %s",
                    dc_object._object_id,
                )

    def __clean_object(self, dc_object):
        """
        @postcondition: Clean object (except if not loaded or being used). Cleaning means set all fields to None to allow
        GC to work.
        @param dc_object: Object to clean.
        """

        """
        Lock object (not locking executions!)
        Lock is needed in case object is being nullified and some threads requires to load it from disk.
        """
        object_id = dc_object._object_id
        self.runtime.lock(object_id)
        try:

            is_loaded = dc_object._is_loaded
            if not is_loaded:
                logger.trace("[==GC==] Not collecting since not loaded.")
                self.release_from_heap(dc_object)
                return

            """ Set loaded flag to false, any current execution that wants to get/set a field must try to load
            object from DB, and lock will control that object is not being cleaned """
            logger.debug("[==GC==] Setting loaded to false from gc %s" % str(object_id))

            dc_object._is_loaded = False

            # Update it
            logger.debug("[==GC==] Updating object %s ", dc_object._object_id)
            self.gc_collect_internal(dc_object)

            logger.debug("[==GC==] Cleaning object %s", dc_object._object_id)

            self.__nullify_object(dc_object)

            """ Object is not dirty anymore """
            dc_object._is_dirty = False

            """
            VERY IMPORTANT (RACE CONDITION)
            If some object was cleaned and removed from GC retained refs, it does NOT mean it was removed
            from Weak references Heap because we will ONLY remove an entry in that Heap if the GC removed it.
            So, if some execution is requested after we remove an entry from retained refs (we cleaned and send
            the object to disk), we check if the
            object is in Heap (see executeImplementation as an example) and therefore, we created a new reference
            making impossible for GC to clean the reference. We will add the object to retained refs
            again once it is deserialized from DB. See DeserializationLib. It's the best solution without Lockers 
            in get and remove in Heap.

            Remove it from Retained refs to allow GC action.
            """
            self.release_from_heap(dc_object)

        finally:
            self.runtime.unlock(object_id)

    def gc_collect_internal(self, object_to_update):
        """
        @postcondition: Update object in db or store it if volatile (and register in LM)
        @param object_to_update: object to update
        """
        try:
            logger.debug("[==GCUpdate==] Updating object %s", object_to_update._object_id)
            """ Call EE update """
            if object_to_update._is_pending_to_register:
                logger.debug(
                    f"[==GCUpdate==] Storing and registering object {object_to_update._object_id}"
                )
                obj_bytes = SerializationLibUtilsSingleton.serialize_for_db_gc(
                    object_to_update, False, None
                )
                self.exec_env.register_and_store_pending(object_to_update, obj_bytes, True)
            else:
                # TODO: use dirty flag to avoid trips to SL? how to update SL graph of references?
                logger.debug(
                    "[==GCUpdate==] Updating dirty object %s ", object_to_update._object_id
                )
                obj_bytes = SerializationLibUtilsSingleton.serialize_for_db_gc(
                    object_to_update, False, None
                )
                self.runtime.update_to_sl(object_to_update._object_id, obj_bytes, True)

        except:
            # do nothing
            traceback.print_exc()
        """ TODO: set datasetid for GC if set by user """

    def run_task(self):
        """
        @postcondition: Check Python VM's memory pressure and clean if necessary. Cleaning means flushing objects, setting
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
            logger.trace("[==GC==] Running GC")

            if self.__check_memory_pressure():
                logger.verbose("System memory is under pressure, proceeding to clean up objects")
                if (
                    logger.isEnabledFor(logging.DEBUG)
                    and tracemalloc is not None
                    and tracemalloc.is_tracing()
                ):
                    logger.debug("Doing a snapshot...")
                    snapshot = tracemalloc.take_snapshot()
                    top_stats = snapshot.statistics("lineno")

                    print("[ Top 10 ]")
                    for stat in top_stats[:10]:
                        print(stat)

                """
                TODO: CORRECT THESE LOGS
                cur_frame = sys._getframe(0)
                logger.debug("[==GC==] Is enabled? %s", str(gc.isenabled()))
                logger.debug("[==GC==] Is retained objects tracked? %s", str(gc.is_tracked(self.retained_objects)))
                logger.debug("[==GC==] Inmemory map %s", str(id(HeapManager.get_heap(self))))
                logger.debug("[==GC==] Retained map %s", str(id(self.retained_objects)))
                logger.debug("[==GC==] Threshold: %s", str(gc.get_threshold()))
                logger.debug("[==GC==] Count: %s", str(gc.get_count()))
                logger.debug("[==GC==] Current frame ID: %s", str(id(cur_frame)))
                """

                # Copy the references in order to process it in a plain fashion
                retained_objects_copy = self.retained_objects[:]
                logger.debug(
                    "Starting iteration with #%d retained objects", len(self.retained_objects)
                )

                while retained_objects_copy:
                    # We iterate through while-pop to ensure that the reference is freed
                    dc_obj = retained_objects_copy.pop()

                    # NOTE: Memory pinned is never set or used
                    # if dc_obj.get_memory_pinned():
                    #     logger.trace(
                    #         "Object %s is memory pinned, ignoring it", dc_obj._object_id
                    #     )
                    #     continue

                    if dc_obj._object_id in self.runtime.volatiles_under_deserialization:
                        logger.trace("[==GC==] Not collecting since it is under deserialization.")
                        continue

                    """ 
                    logger.debug("[==GC==] Object address in memory: %s", str(id(dc_obj)))
                    logger.debug("[==GC==] Is tracked? %s", str(gc.is_tracked(dc_obj)))
                    for r in gc.get_referents(dc_obj):
                        if r == self.retained_objects:
                            logger.debug("[==GC==] REFERENT BEFORE CLEAN FOR %s is retained map. ", (dc_obj._object_id))
                        elif r == HeapManager.get_heap(self):
                            logger.debug("[==GC==] REFERENT BEFORE CLEAN FOR %s is inmemory map. ", (dc_obj._object_id)) 
                        else:
                            logger.debug("[==GC==] REFERENT BEFORE CLEAN FOR %s is: %s ", (dc_obj._object_id, str(id(r))))
                            # logger.debug("[==GC==] REFERENT BEFORE CLEAN FOR %s is: %s ", (dc_obj._object_id, pprint.pformat(r)))
                    for r in gc.get_referrers(dc_obj):
                        if r == self.retained_objects:
                            logger.debug("[==GC==] REFERRER BEFORE CLEAN FOR %s is retained map. ", (dc_obj._object_id))
                        elif r == HeapManager.get_heap(self):
                            logger.debug("[==GC==] REFERRER BEFORE CLEAN FOR %s is inmemory map. ", (dc_obj._object_id))
                        else:
                            logger.debug("[==GC==] REFERRER BEFORE CLEAN FOR %s is: %s ", (dc_obj._object_id, str(id(r))))
                            # logger.debug("[==GC==] REFERRER BEFORE CLEAN FOR %s is: %s ", (dc_obj._object_id, pprint.pformat(r)))
                    """
                    self.__clean_object(dc_obj)
                    """
                    for r in gc.get_referents(dc_obj):
                        if r == self.retained_objects:
                            logger.debug("[==GC==] REFERENT FOR %s is retained map. ", (dc_obj._object_id))
                        elif r == HeapManager.get_heap(self):
                            logger.debug("[==GC==] REFERENT FOR %s is inmemory map. ", (dc_obj._object_id))
                        else:
                            logger.debug("[==GC==] REFERENT FOR %s is: %s ", (dc_obj._object_id, str(id(r))))
                            # logger.debug("[==GC==] REFERENTS FOR %s is: %s ", (dc_obj._object_id, pprint.pformat(r)))
                    """
                    """
                    for r in gc.get_referrers(dc_obj):
                        if r == self.retained_objects:
                            logger.debug("[==GC==] REFERRER FOR %s is retained map. ", (dc_obj._object_id))
                        elif r == HeapManager.get_heap(self):
                            logger.debug("[==GC==] REFERRER FOR %s is inmemory map. ", (dc_obj._object_id))
                        else:
                            logger.debug("[==GC==] ID REFERRER FOR %s is: %s ", (dc_obj._object_id, str(id(r))))
                            logger.debug("[==GC==] REFERRER FOR %s are: %s ", (dc_obj._object_id, pprint.pformat(r)))
                    """
                    del dc_obj  # Remove reference from Frame

                    # Big heaps
                    n = gc.collect()
                    if logger.isEnabledFor(logging.DEBUG) or logger.isEnabledFor(logging.TRACE):
                        if n > 0:
                            logger.debug("[==GC==] Collected %d", n)
                        else:
                            logger.trace("[==GC==] No objects collected")
                        if gc.garbage:
                            logger.debug("[==GC==] Uncollectable: %s", gc.garbage)
                        else:
                            logger.trace("[==GC==] No uncollectable objects")

                    # Check memory
                    at_ease = self.__check_memory_ease()
                    if at_ease:
                        logger.trace("[==GC==] Not collecting since memory is 'at ease' now")
                        break
                    if self.is_flushing_all:
                        logger.debug("[==GC==] Interrupted due to flush all.")
                        break
                else:
                    # This block is only entered when the while has finished (with no break statement)
                    # which means that all the objects have been iterated
                    logger.warning(
                        "I did my best and ended up cleaning all retained_objects. This typically means"
                        " that there is a huge global memory pressure. Problematic."
                    )
                logger.debug(
                    "Finishing iteration with #%d retained objects", len(self.retained_objects)
                )

                self.cleanReferencesAndLockers()

                # For cyclic references
                n = gc.collect()

                if logger.isEnabledFor(logging.DEBUG) or logger.isEnabledFor(logging.TRACE):
                    if retained_objects_copy:
                        logger.debug(
                            "There are #%d remaining objects after Garbage Collection",
                            len(retained_objects_copy),
                        )
                    if n > 0:
                        logger.debug("[==GC==] Finally Collected %d", n)
                    else:
                        logger.trace("[==GC==] No objects collected")
                    if gc.garbage:
                        logger.debug("[==GC==] Uncollectable: %s", gc.garbage)
                    else:
                        logger.trace("[==GC==] No uncollectable objects")

                del retained_objects_copy

                if (
                    logger.isEnabledFor(logging.DEBUG)
                    and tracemalloc is not None
                    and tracemalloc.is_tracing()
                ):
                    logger.debug("Doing a snapshot...")
                    snapshot2 = tracemalloc.take_snapshot()

                    top_stats = snapshot2.compare_to(snapshot, "lineno")

                    print("[ Top 10 differences ]")
                    for stat in top_stats[:10]:
                        print(stat)
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

        logger.debug("[==FlushAll==] Number of objects in Heap: %s", self.heap_size())
        for object_to_update in self.retained_objects:
            self.gc_collect_internal(object_to_update)

        return
