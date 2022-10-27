""" Class description goes here. """

"""
Created on 1 feb. 2018

@author: dgasull
"""
import importlib

from dataclay.runtime.ExecutionGateway import ExecutionGateway
from dataclay.loader.DataClayObjectLoader import DataClayObjectLoader
from dataclay.serialization.lib.DeserializationLibUtils import DeserializationLibUtilsSingleton


class ClientObjectLoader(DataClayObjectLoader):
    """
    @summary: This class is responsible to create DataClayObjects and load them with data coming from different resources. All possible
    constructions of DataClayObject should be included here. All possible "filling instance" use-cases should be managed here.
    Most lockers should be located here.
    """

    def __init__(self, theruntime):
        """
        @postcondition: Constructor of the object
        @param theruntime: Runtime being managed
        """
        DataClayObjectLoader.__init__(self, theruntime)

    def new_instance(self, class_id, object_id):
        """
        TODO: Refactor this function
        """
        self.logger.verbose("Creating an instance from the class: {%s}", class_id)

        try:
            # Note that full_class_name *includes* namespace (Python-specific behaviour)
            full_class_name = self.runtime.local_available_classes[class_id]
        except KeyError:
            raise RuntimeError(
                "Class {%s} is not amongst the locally available classes, "
                "check contracts and/or initialization" % class_id
            )

        package_name, class_name = full_class_name.rsplit(".", 1)
        m = importlib.import_module(package_name)
        klass = getattr(m, class_name)

        return ExecutionGateway.new_dataclay_instance(
            klass, deserializing=True, object_id=object_id
        )

    def get_or_new_volatile_instance_and_load(
        self, class_id, object_id, hint, obj_with_data, ifacebitmaps
    ):
        """
        @postcondition: Get from Heap or create a new volatile in EE and load data on it.
        @param class_id: id of the class of the object
        @param object_id: id of the object
        @param hint: hint of the object
        @param obj_with_data: data of the volatile
        @param ifacebitmaps: interface bitmaps
        """
        """
        RACE CONDITION DESIGN
        There are two objects A and B, A -> B, A is persistent and B is volatile.
        There are two threads T1 and T2, T1 is executing a method on A that uses B, when deserializing A, B is loaded into
        heap as a persistent object (all associations are persistent). However, it is actually a volatile send by T2.
        When a volatile server is received and a persistent instance is found, this persistent instance should be "replaced"
        by the new volatile server.
        """
        self.runtime.lock(object_id)
        self.logger.verbose(
            "Get or create new client volatile instance with object id %s in Heap ", str(object_id)
        )
        try:
            """Double check for race conditions"""
            volatile_obj = self.runtime.get_from_heap(object_id)
            if volatile_obj is None:
                volatile_obj = self.new_instance_internal(class_id, object_id, hint)

            """ Deserialize volatile """
            DeserializationLibUtilsSingleton.deserialize_object_with_data_in_client(
                obj_with_data,
                volatile_obj,
                ifacebitmaps,
                self.runtime,
                self.runtime.session.id,
            )

            # WARNING: RACE CONDITION at EE - during deserialization of volatiles the
            # object may be created and
            # loaded in Heap but not "fully deserialized" yet so even if any execution find
            # it in the
            # heap, object might
            # be not ready (null fields, and no, so is loaded cannot
            # be true till object was fully deserialized)
            volatile_obj.initialize_object_as_volatile()
        finally:
            self.runtime.unlock(object_id)

        return volatile_obj
