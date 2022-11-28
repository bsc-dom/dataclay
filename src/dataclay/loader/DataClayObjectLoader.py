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
