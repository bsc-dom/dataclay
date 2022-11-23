""" Class description goes here. """

"""
Created on 1 feb. 2018

@author: dgasull
"""
import time
import traceback

from dataclay.loader.DataClayObjectLoader import DataClayObjectLoader
from dataclay.conf import settings


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

    def _get_from_db_and_fill(self, object_to_fill):
        """
        @postcondition: Get from DB and deserialize into instance
        @param object_to_fill: Instance to fill
        """
        object_id = object_to_fill._dc_id
        self.logger.debug("Object %s being loaded from DB", object_id)
        obj_bytes = self.runtime.get_from_sl(object_id)
        DeserializationLibUtilsSingleton.deserialize_object_from_db(
            object_to_fill, obj_bytes, self.runtime
        )
        object_to_fill._dc_master_ee_id = self.runtime.get_hint()
        self.logger.debug("Object %s loaded from DB", object_id)

    def get_or_new_instance_from_db(self, object_id, retry):
        raise ("Need to be rafactored")
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
        self.logger.debug(
            "Get or create new instance from SL with object id %s in Heap ", str(object_id)
        )
        obtained = False
        wait_time = 0
        sleep_time = settings.SLEEP_WAIT_REGISTERED / 1000
        instance = None
        while not obtained:
            self.runtime.lock(object_id)
            try:
                instance = self.runtime.inmemory_objects[object_id]
                if instance is None:
                    obj_bytes = self.runtime.get_from_sl(object_id)
                    msg = DeserializationLibUtilsSingleton.deserialize_grpc_message_from_db(
                        obj_bytes
                    )
                    metadata = get_metadata(msg.metadata)
                    instance_class_id = metadata.tags_to_class_ids[0]
                    instance = self.new_instance(instance_class_id, object_id)
                    instance.initialize_object_as_persistent()
                    DeserializationLibUtilsSingleton.deserialize_object_from_db_bytes_aux(
                        instance, metadata, msg.data, self.runtime
                    )
                    instance._dc_master_ee_id = self.runtime.get_hint()
                    self.logger.debug("Object %s deserialized", object_id)

                if not instance._dc_is_loaded:
                    self._get_from_db_and_fill(instance)

                obtained = True
            except:
                self.logger.debug(
                    "Received error while retrieving object %s", object_id, exc_info=True
                )
                if not retry or wait_time > settings.TIMEOUT_WAIT_REGISTERED:
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

        raise ("Not implemented")
        object_id = instance._dc_id
        loaded = False
        wait_time = 0
        sleep_time = settings.SLEEP_WAIT_REGISTERED / 1000
        while not loaded and wait_time < settings.TIMEOUT_WAIT_REGISTERED:
            self.runtime.lock(object_id)
            try:
                """double check for race-conditions"""
                if not instance._dc_is_loaded:
                    self._get_from_db_and_fill(instance)
                loaded = True
            except Exception as ex:
                traceback.print_exc()
                if not retry or wait_time > settings.TIMEOUT_WAIT_REGISTERED:
                    raise ex
                self.logger.debug("Object %s not found in DB. Waiting and retry...", object_id)
                wait_time = wait_time + sleep_time
                time.sleep(sleep_time)
            finally:
                self.runtime.unlock(object_id)
