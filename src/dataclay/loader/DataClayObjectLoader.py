
""" Class description goes here. """

'''
Created on 1 feb. 2018

@author: dgasull
'''
import logging
from abc import ABCMeta, abstractmethod
import six

""" Make this class abstract """


@six.add_metaclass(ABCMeta)
class DataClayObjectLoader(object):
    """
    @summary: This class is responsible to create DataClayObjects and load them with data coming from different resources. All possible
    constructions of DataClayObject should be included here. All possible "filling instance" use-cases should be managed here.
    Most lockers should be located here.
    """
    
    """ Logger """
    logger = logging.getLogger(__name__)
    
    def __init__(self, theruntime):
        """
        Constructor
        @param theruntime: Runtime being managed. 
        """ 
        """ Runtime being monitorized. Java uses abstract functions to get the field in the proper type (EE or client) due to type-check. Not needed here. """
        self.runtime = theruntime
    
    @abstractmethod
    def new_instance(self, class_id, object_id):
        """ 
        @postcondition: create a new instance using proper class. This function is abstract.
        @param class_id: id of the class of the object.
        @param object_id: id of the object to get/create
        @return instance with object id provided
        """
        pass

    def new_instance_internal(self, class_id, object_id, hint): 
        """ 
        @postcondition: create a new instance. 
        @param class_id: id of the class of the object. Can be none. If none, means that class_id should be obtained from metadata of the obj.
        @param object_id: id of the object to get/create
        @param hint: hint of the object in case it is created. 
        @return instance with object id provided
        """
        obj = self.new_instance(class_id, object_id)
        if hint is not None:
            """ set hint if not none. If none do not set it to avoid overriding!"""
            obj.set_hint(hint)
            
        return obj
    
    def get_or_new_persistent_instance(self, class_id, object_id, hint):
        """
        @postcondition: check if instance is in heap. if so, return it. otherwise, create a new persistent instance with proper flags.
        @param class_id: id of class of the instance. Can be none. If none, means that class_id should be obtained from metadata of the obj.
        @param object_id: id of the object to get/create
        @param hint: hint of the object in case it is created. 
        @return instance with object id provided
        """
        self.logger.verbose("Get or create new persistent instance with object id %s in Heap ", str(object_id))
        obj = self.runtime.get_from_heap(object_id)
        if obj is None: 
            self.logger.debug("Object %s not found in heap", object_id)
            self.runtime.lock(object_id)
            try:
                """ Double check for race conditions. """
                obj = self.runtime.get_from_heap(object_id)
                if obj is None: 
                    self.logger.debug("Creating new instance for %s", object_id)
                    obj = self.new_instance_internal(class_id, object_id, hint)
                
                """ == Set Flags == """ 
                obj.initialize_object_as_persistent()

            finally:
                self.runtime.unlock(object_id)
        else: 
            self.logger.debug("Object %s found in heap", object_id)
            if obj is None: 
                self.logger.debug("Object %s found in heap IS NONE", object_id)
        return obj
    
    @abstractmethod
    def get_or_new_volatile_instance_and_load(self, class_id, object_id, hint, obj_with_data, ifacebitmaps):
        """
        @postcondition: Get from Heap or create a new volatile in EE and load data on it.
        @param class_id: id of the class of the object
        @param object_id: id of the object
        @param hint: hint of the object 
        @param obj_with_data: data of the volatile 
        @param ifacebitmaps: interface bitmaps 
        """
        pass
    
