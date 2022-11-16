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

    def run_task(self):
        self.cleanReferencesAndLockers()
