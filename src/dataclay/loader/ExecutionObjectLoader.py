
""" Class description goes here. """

'''
Created on 1 feb. 2018

@author: dgasull
'''
from dataclay.loader.DataClayObjectLoader import DataClayObjectLoader
import importlib
import traceback
import logging
import time
from dataclay.commonruntime.ExecutionGateway import ExecutionGateway
from dataclay.serialization.lib.DeserializationLibUtils import DeserializationLibUtilsSingleton
from dataclay.communication.grpc.Utils import get_metadata
from dataclay.util.classloaders.ClassLoader import load_metaclass_info
from dataclay.commonruntime.Runtime import getRuntime
from dataclay.util import Configuration


class ExecutionObjectLoader(DataClayObjectLoader):
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
        
        self.logger.debug("Creating an instance from the class: {%s}", class_id)
    
        # Obtain the class name from the MetaClassInfo
        full_class_name, namespace = load_metaclass_info(class_id)
        self.logger.debug("MetaClassID {%s}: full class name `%s` | namespace `%s`",
                     class_id, full_class_name, namespace)
    
        class_name_parts = full_class_name.rsplit(".", 1)
    
        if len(class_name_parts) == 2:
            package_name, class_name = class_name_parts
            module_name = "%s.%s" % (namespace, package_name)
        else:
            class_name = class_name_parts[0]
            module_name = "%s" % namespace
    
        try:
            import sys
            m = importlib.import_module(module_name)
        except ImportError:
            self.logger.error("new_instance failed due to ImportError")
            self.logger.error("load_metaclass_info returned: full_class_name=%s, namespace=%s",
                         full_class_name, namespace)
            self.logger.error("Trying to import: %s", module_name)
    
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.error("DEBUG Stacktrace", exc_info=True)
    
            # # Very ugly, but required for some deep debugging strange behaviour
            # import sys
            # logger.error("The import path is: %s", sys.path)
            #
            # import subprocess
            # logger.error("`ls -laR %s` yields the following:\n%s",
            #              settings.deploy_path_source,
            #              subprocess.check_output("ls -laR %s" % settings.deploy_path_source,
            #                                      shell=True)
            #              )
    
            # Let the exception raise again, untouched
            raise
    
        klass = getattr(m, class_name)
        return klass.new_dataclay_instance(deserializing=True, object_id=object_id)
    
    def get_or_new_persistent_instance(self, class_id, object_id, hint):
        return super(ExecutionObjectLoader, self).get_or_new_persistent_instance(class_id, object_id, hint)
    
    def _get_from_db_and_fill(self, object_to_fill):
        """
        @postcondition: Get from DB and deserialize into instance
        @param object_to_fill: Instance to fill
        """
        object_id = object_to_fill.get_object_id()
        self.logger.debug("Object %s being loaded from DB", object_id)
        obj_bytes = self.runtime.get_from_sl(object_id)
        DeserializationLibUtilsSingleton.deserialize_object_from_db(object_to_fill, obj_bytes, self.runtime)
        object_to_fill.set_hint(self.runtime.get_hint())
        self.logger.debug("Object %s loaded from DB", object_id)
    
    def get_or_new_instance_from_db(self, object_id, retry):
        """
        @postcondition: Get object from memory or database and WAIT in case we are still waiting for it to be persisted.
        @param object_id: ID of the object to get
        @param retry: indicates if we should retry and wait 
        @param class_id: Can be none. Class ID of the object to get. In order to avoid looking for metadata.
        @return: the object 
        """
        
        """
        Retry while object is not 'registered' (not talking about 'stored'!)
        IMPORTANT: This is different than waiting for an object to be stored
        If the object is not registered we still do not know the class id of the instance
        in which to load the bytes.
        Due to concurrency we should read bytes and deserialize and unlock.
        Therefore there is Two waiting loops. (can we do it better?, more locking?)
        """ 
        self.logger.verbose("Get or create new instance from SL with object id %s in Heap ", str(object_id))
        obtained = False 
        wait_time = 0
        sleep_time = Configuration.SLEEP_WAIT_REGISTERED / 1000
        instance = None
        while not obtained:
            self.runtime.lock(object_id)
            try:
                instance = self.runtime.get_from_heap(object_id)
                if instance is None: 
                    obj_bytes = self.runtime.get_from_sl(object_id)
                    msg = DeserializationLibUtilsSingleton.deserialize_grpc_message_from_db(obj_bytes)
                    metadata = get_metadata(msg.metadata)
                    instance_class_id = metadata[1][0]
                    instance = self.new_instance(instance_class_id, object_id)
                    instance.initialize_object_as_persistent()
                    DeserializationLibUtilsSingleton.deserialize_object_from_db_bytes_aux(instance, metadata, msg.data, self.runtime)
                    instance.set_hint(self.runtime.get_hint())
                    self.logger.debug("Object %s deserialized", object_id)

                if not instance.is_loaded():
                    self._get_from_db_and_fill(instance)

                obtained = True
            except:
                self.logger.debug("Received error while retrieving object %s", object_id, exc_info=True)
                if not retry or wait_time > Configuration.TIMEOUT_WAIT_REGISTERED:
                    raise
                
                wait_time = wait_time + sleep_time
                self.logger.debug("Object %s not found in DB. Waiting and retry...", object_id)
                time.sleep(sleep_time)
            finally:
                self.runtime.unlock(object_id)
        
        return instance
                
    def load_object_from_db(self, instance, retry):
        """
        @postcondition: Load DataClayObject from Database
        @param instance: DataClayObject instance to fill
        @param retry: Indicates retry loading in case it is not in db.
        """
        
        object_id = instance.get_object_id()
        loaded = False 
        wait_time = 0
        sleep_time = Configuration.SLEEP_WAIT_REGISTERED / 1000
        while not loaded and wait_time < Configuration.TIMEOUT_WAIT_REGISTERED:
            self.runtime.lock(object_id)
            try:
                """ double check for race-conditions"""
                if not instance.is_loaded():
                    self._get_from_db_and_fill(instance)
                loaded = True
            except Exception as ex: 
                traceback.print_exc()
                if not retry or wait_time > Configuration.TIMEOUT_WAIT_REGISTERED:
                    raise ex
                self.logger.debug("Object %s not found in DB. Waiting and retry...", object_id)
                wait_time = wait_time + sleep_time
                time.sleep(sleep_time)
            finally:
                self.runtime.unlock(object_id)
                
    def get_or_new_volatile_instance_and_load(self, class_id, object_id, hint, obj_with_data, ifacebitmaps):
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
        try:
            """ Double check for race conditions """
            self.logger.verbose("Get or create new volatile instance in EE with object id %s in Heap ", str(object_id))
            volatile_obj = self.runtime.get_from_heap(object_id)
            if volatile_obj is None: 
                volatile_obj = self.new_instance_internal(class_id, object_id, hint)
                    
            """ Deserialize volatile """ 
            DeserializationLibUtilsSingleton.deserialize_object_with_data(obj_with_data, volatile_obj, ifacebitmaps, self.runtime,
                                             self.runtime.get_session_id(),
                                             True)
            
            self.logger.debug("Object %s deserialized", object_id)

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
        
