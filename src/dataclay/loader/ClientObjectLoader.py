""" Class description goes here. """

"""
Created on 1 feb. 2018

@author: dgasull
"""
import importlib

from dataclay import DataClayObject
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

        return DataClayObject.new_dataclay_instance(klass, deserializing=True, object_id=object_id)
