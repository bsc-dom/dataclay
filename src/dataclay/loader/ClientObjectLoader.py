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
