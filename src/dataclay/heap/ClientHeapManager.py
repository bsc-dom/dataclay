
""" Class description goes here. """

'''
Created on 26 ene. 2018

@author: dgasull
'''
from dataclay.heap.HeapManager import HeapManager
from threading import Timer


class ClientHeapManager(HeapManager):
    """
    @summary: This class is intended to manage all dataClay objects in Client runtime's memory.
    """
    
    def __init__(self, theruntime):
        """
        @postcondition: Constructor of the object 
        @param theruntime: Runtime being managed 
        """ 
        HeapManager.__init__(self, theruntime)
        self.logger.debug("CLIENT HEAP MANAGER created")
            
    def add_to_heap(self, dc_object):
        """
        @postcondition: the object is added to dataClay's heap
        @param dc_object: object to add to the heap 
        """
        HeapManager._add_to_inmemory_map(self, dc_object)     
        
    def flush_all(self): 
        """ 
        @postcondition: Does nothing. This function is intended to be used only in Execution Environment. Since 
        Heap Manager is an abstract class, we define this method as an "empty" method. Maybe I am missing some 
        better way to do that? (dgasull)
        """
        return
    
    def run_task(self): 
        self.cleanReferencesAndLockers()
