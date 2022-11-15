""" Class description goes here. """

"""
Created on 26 ene. 2018

@author: dgasull
"""
import logging
from threading import Timer

from dataclay.heap.heap_manager import HeapManager
from dataclay_common import utils

logger = utils.LoggerEvent(logging.getLogger(__name__))


class ClientHeapManager(HeapManager):
    """This class is intended to manage all dataClay objects in Client runtime's memory."""

    def __init__(self, theruntime):
        super().__init__(theruntime)
        logger.debug("CLIENT HEAP MANAGER created")

    def add_to_heap(self, dc_object):
        """add object to dataClay's heap"""
        super()._add_to_inmemory_map(dc_object)

    def flush_all(self):
        """Does nothing.

        This function is intended to be used only in Execution Environment. Since
        Heap Manager is an abstract class, we define this method as an "empty" method. Maybe I am missing some
        better way to do that? (dgasull)
        """
        return

    def run_task(self):
        self.cleanReferencesAndLockers()
