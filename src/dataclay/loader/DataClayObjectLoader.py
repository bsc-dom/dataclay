""" Class description goes here. """

"""
Created on 1 feb. 2018

@author: dgasull
"""
import logging
from abc import ABC, abstractmethod

""" Make this class abstract """


class DataClayObjectLoader(ABC):
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
            """set hint if not none. If none do not set it to avoid overriding!"""
            obj._master_ee_id = hint

        return obj
