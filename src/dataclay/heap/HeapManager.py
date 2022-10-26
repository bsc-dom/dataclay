""" Class description goes here. """

"""
Created on Jan 25, 2018

@author: dgasull
"""
import logging
import threading
from abc import ABC, abstractmethod
from weakref import WeakValueDictionary

from dataclay_common import utils

from dataclay.util import Configuration

""" Make this class abstract """

logger = utils.LoggerEvent(logging.getLogger(__name__))


class HeapManager(threading.Thread, ABC):
    """
    @summary: This class is intended to manage all dataClay objects in runtime's memory.
    """

    logger = None

    def __init__(self, theruntime):
        """Constructor of the object called from sub-class

        Args:
            theruntime: Runtime being managed
        """
        threading.Thread.__init__(self)

        # Memory objects. This dictionary must contain all objects in runtime memory (client or server), as weakrefs.
        self.inmemory_objects = WeakValueDictionary()

        # Event object to communicate shutdown
        self._finished = threading.Event()

        # Runtime being monitorized.
        self.runtime = theruntime

        self.daemon = True
        logger.debug("HEAP MANAGER created.")

    def shutdown(self):
        """Stop this thread"""
        logger.debug("HEAP MANAGER shutdown request received.")
        self._finished.set()

    def run(self):
        """Overrides run function"""
        gc_check_time_interval_seconds = Configuration.MEMMGMT_CHECK_TIME_INTERVAL / 1000.0
        while True:
            logger.debug("HEAP MANAGER THREAD is awake...")
            if self._finished.is_set():
                break
            self.run_task()

            # sleep for interval or until shutdown
            logger.debug("HEAP MANAGER THREAD is going to sleep...")
            self._finished.wait(gc_check_time_interval_seconds)

        logger.debug("HEAP MANAGER THREAD Finished.")

    def _add_to_inmemory_map(self, dc_object):
        """add object to inmemory map"""
        oid = dc_object.get_object_id()
        self.inmemory_objects[oid] = dc_object

    def remove_from_heap(self, object_id):
        """Remove reference from Heap.

        Even if we remove it from the heap the object won't be Garbage collected
        untill HeapManager flushes the object and releases it.
        """
        self.inmemory_objects.pop(object_id)

    def get_from_heap(self, object_id):
        """Get from heap.
        Args:
            object_id: id of object to get from heap
        Returns:
            Object with id provided in heap or None if not found.
        """
        try:
            obj = self.inmemory_objects[object_id]
            logger.debug("Hit in Heap object %s" % str(object_id))
            return obj
        except KeyError:
            logger.debug("Miss in Heap object %s" % str(object_id))
            return None

    def exists_in_heap(self, object_id):
        return object_id in self.inmemory_objects

    def heap_size(self):
        return len(self.inmemory_objects)

    def count_loaded_objs(self):
        num_loaded_objs = 0
        for obj in self.inmemory_objects.values():
            if obj.is_loaded():
                num_loaded_objs = num_loaded_objs + 1
        return num_loaded_objs

    @abstractmethod
    def flush_all(self):
        pass

    @abstractmethod
    def run_task(self):
        pass

    def cleanReferencesAndLockers(self):
        """Clean references and lockers not being used."""
        self.runtime.locker_pool.cleanLockers()
