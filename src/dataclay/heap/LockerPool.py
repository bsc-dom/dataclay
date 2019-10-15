
""" Class description goes here. """

""" This is a pool of lockers to manage concurrent actions in shared objects in dataClay """

# Created on Jan 23, 2018

import logging
import threading

__author__ = "dgasull"


class LockerPool(object):
    logger = logging.getLogger('dataclay.LockerPool')

    def __init__(self):
        # Lockers
        self.lockers = dict()

        # Lock for the pool
        self.locker = threading.Lock()
    
    def lock(self, object_id):
        """ 
        Locking design.
        ==============
        If we are using CPython as interpreter, GIL can 'stop' current thread in the middle of a serialization and 
        start sleeping thread in the middle of other action in same object and we can have race conditions or many other
        problems. Therefore we need to lock the objects. 
        
        CPython guarantees that get/put in maps are atomic but not 'get and create if needed'. In our case,
        imagine the code below and two threads located in the lines specified as comments:
        
        if not object_id in self.lockers: #ObjectID is the same for both threads 
            lock = threading.RLock() #Thread 2 is here
            self.lockers.put(object_id, lock) #Thread 1 is here 

        Thread 1 was the first to arrive and find out that there is no locker for the object "he" wants to lock. Therefore,
        Thread 1 creates a new locker. During creation of the Locker, Thread 2 arrives and find no locker.
        Thread 1 put the locker in the ConcurrentHashMap. Thread 2 also creates a locker and overrides Thread 1's locker.
        This is a problem we should solve since both threads are using differents lockers for the same object, loosing the
        concept of lockers.
        
        
        In order to solve that we need to create an atomic set of operations, from now on called "synchronized block of code". 
        We could create a synchronized block based in ObjectID since Threads accessing/creating lockers 
        with same ObjectIDs can have a problem. However, our current implementation does NOT
        guarantee that two ObjectIDs representing same ID (ie with same UUID) are the same instances in memory.
        Therefore we cannot create a synchronized block using ObjectID. We could think about forcing all ObjectIDs to be
        unique ("same-instances") in memory (only one instance of ObjectID representing an object) but it ends in having same 
        synchronization but during the creation of the ObjectID (it can be in any request). Now, adding the synchronized block here is better
        in order to only lock 'if-needed' instead of doing it at creation time.
        
        Then, what should we synchronize? Anything that is 'common' for all threads. In our case, the Locker Pool is unique
        per runtime (server or client). For example:
        
        
        self.lock.acquire() #Lock is created during construction of the LockerPool, "lock = threading.RLock()" It's a reentrant lock!
        if not object_id in self.lockers: 
            lock = threading.RLock() 
            self.lockers.put(object_id, lock)        
        self.lock.release()
    
        
        This would solve our problem. But it's a bottleneck! All threads that wants to lock anything, will end up locking
        the pool. Since our problem is just at 'creation' of lockers we move the synchronized block inside the if and we
        apply the design of 'double-check' of lockers:
        
        if not object_id in self.lockers: 
            self.lock.acquire() # ensure only one locker is created per object
            if not object_id in self.lockers: 
                lock = threading.RLock() 
                self.lockers.put(object_id, lock)  
            self.lock.release()
        else:
            lock = self.lockers.get(object_id)

        
        All threads that try to 'create' lockers are going to have the overhead of synchronizing the locker pool. However,
        it is not our critical path, since in our critical path everything is in cache and lockers exist.
        
        """
        try:
            obj_lock = self.lockers[object_id]
        except KeyError:
            with self.locker:  # ensure only one locker is created per object
                if object_id not in self.lockers:
                    obj_lock = threading.RLock()
                    self.lockers[object_id] = obj_lock
                else:
                    # race condition averted!
                    obj_lock = self.lockers[object_id]

        # Locks the object     
        obj_lock.acquire()
        
    def unlock(self, object_id):
        """
        Unlock object with object ID provided. 
        If the locker does not exist, it means it was already released and cleaned from memory. Since our lockers are 
        Reentrant, there can be many 'unlock' calls unlocking the same locker. If our Memory manager wants to clean a locker,
        it checks if it is unlocked and if so, it removes it. Therefore, just unlock if exists. 
        
        """         
        try:
            self.lockers[object_id].release()
        except KeyError:
            pass
            
    def cleanLockers(self):
        """
        Clean lockers. This function should be called only from Memory manager in order to clean the lockers alive in memory and
        avoid having thousands of 'dead' lockers occupying memory. Since it is only called from ONE thread, it is only possible
        that some thread wants to create a Locker (see lock function) at same time we want to remove it. Therefore, we create
        a synchronized block for that. 
        """
        cleaned_lockers = 0
        
        # We create a copy of the locker_ids, (the key-set) and we remove them if needed.
        locker_ids = list(self.lockers.keys())
        for object_id in locker_ids:
            with self.locker:  # ensure we are not cleaning lockers during lockers creation.
                pass
                # locker = self.lockers.get(object_id)
                # if not locker._
                #    self.lockers.pop(object_id)
                #    cleaned_lockers = cleaned_lockers + 1
