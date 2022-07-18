""" Class description goes here. """

"""
Created on Jan 25, 2018

@author: dgasull
"""
from weakref import WeakValueDictionary
import logging
from abc import ABCMeta, abstractmethod
import threading
from dataclay.util import Configuration
import six
from uuid import UUID

""" Make this class abstract """


@six.add_metaclass(ABCMeta)
class HeapManager(threading.Thread):
    """
    @summary: This class is intended to manage all dataClay objects in runtime's memory.
    """

    """ Logger """
    logger = None

    def __init__(self, theruntime):
        """
        @postcondition: Constructor of the object called from sub-class
        @param theruntime: Runtime being managed
        """
        """ Memory objects. This dictionary must contain all objects in runtime memory (client or server), as weakrefs. """
        self.inmemory_objects = WeakValueDictionary()
        threading.Thread.__init__(self)
        self._finished = threading.Event()
        """ Runtime being monitorized. Java uses abstract functions to get the field in the proper type (EE or client) due to type-check. Not needed here. """
        self.runtime = theruntime
        self.logger = logging.getLogger(__name__)
        self.daemon = True
        self.logger.debug("HEAP MANAGER created.")

    def get_heap(self):
        return self.inmemory_objects

    def shutdown(self):
        """Stop this thread"""
        self.logger.debug("HEAP MANAGER shutdown request received.")
        self._finished.set()

    def run(self):
        """
        @postcondition: Overrides run function
        """
        gc_check_time_interval_seconds = Configuration.MEMMGMT_CHECK_TIME_INTERVAL / 1000.0
        while 1:
            self.logger.trace("HEAP MANAGER THREAD is awake...")
            if self._finished.isSet():
                break
            self.run_task()

            # sleep for interval or until shutdown
            self.logger.trace("HEAP MANAGER THREAD is going to sleep...")
            self._finished.wait(gc_check_time_interval_seconds)

        self.logger.debug("HEAP MANAGER THREAD Finished.")

    def _add_to_inmemory_map(self, dc_object):
        """
        @postcondition: the object is added to inmemory map
        @param dc_object: object to add
        """
        oid = dc_object.get_object_id()
        self.inmemory_objects[UUID(str(oid))] = dc_object

    def remove_from_heap(self, object_id):
        """
        @postcondition: Remove reference from Heap. Even if we remove it from the heap,
        the object won't be Garbage collected till HeapManager flushes the object and releases it.
        @param object_id: id of object to remove from heap
        """
        self.inmemory_objects.pop(UUID(str(object_id)))

    def get_from_heap(self, object_id):
        """
        @postcondition: Get from heap.
        @param object_id: id of object to get from heap
        @return Object with id provided in heap or None if not found.
        """
        try:
            obj = self.inmemory_objects[UUID(str(object_id))]
            self.logger.debug("Hit in Heap object %s" % str(object_id))
            return obj
        except KeyError:
            self.logger.debug("Miss in Heap object %s" % str(object_id))
            return None

    def exists_in_heap(self, object_id):
        """
        @postcondition: Exists from heap.
        @param object_id: id of object to get from heap
        @return True if exists. False otherwise.
        """
        try:
            if self.inmemory_objects[UUID(str(object_id))] is None:
                return False
            else:
                return True
        except KeyError:
            return False

    def heap_size(self):
        """
        @postcondition: Get heap size.
        @return Heap size
        """
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
        """
        @postcondition: Clean references and lockers not being used.
        """
        self.runtime.locker_pool.cleanLockers()
