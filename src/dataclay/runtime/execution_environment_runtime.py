""" Class description goes here. """

import datetime
import logging
import threading
import time

from dataclay.heap.ExecutionEnvironmentHeapManager import ExecutionEnvironmentHeapManager
from dataclay.loader.ExecutionObjectLoader import ExecutionObjectLoader
from dataclay.runtime.dataclay_runtime import DataClayRuntime
from dataclay.runtime import settings
from dataclay.serialization.lib.SerializationLibUtils import SerializationLibUtilsSingleton
from dataclay.util import Configuration
from dataclay_common.metadata_service import MetadataService
from dataclay.dataclay_object import DataClayObject
from dataclay.DataClayObjProperties import (
    DCLAY_GETTER_PREFIX,
    DCLAY_PROPERTY_PREFIX,
    DCLAY_SETTER_PREFIX,
)

__author__ = "Alex Barcelo <alex.barcelo@bsc.es>"
__copyright__ = "2015 Barcelona Supercomputing Center (BSC-CNS)"

logger = logging.getLogger(__name__)

current_milli_time = lambda: int(round(time.time() * 1000))


class ExecutionEnvironmentRuntime(DataClayRuntime):
    def __init__(self, theexec_env, etcd_host, etcd_port):

        # Execution Environment using this runtime.
        # TODO: This is a bad design that could produce circular imports
        # Remove it and think a better desing.
        self.execution_environment = theexec_env

        # Initialize parent
        metadata_service = MetadataService(etcd_host, etcd_port)
        dataclay_object_loader = ExecutionObjectLoader(self)
        dataclay_heap_manager = ExecutionEnvironmentHeapManager(self)

        super().__init__(metadata_service, dataclay_heap_manager, dataclay_object_loader)

        # References hold by sessions. Resource note: Maximum size of this map is maximum number of objects allowed in EE x sessions.
        # Also, important to think what happens if one single session is associated to two client threads? use case?
        # should we allow that?
        # Must be thread-safe.
        self.references_hold_by_sessions = dict()

        # Sessions in quarantine. note: maximum size of this map is max number of sessions per EE: This map is needed to solve a race
        # condition in Global Garbage collection (@see getReferenceCounting).
        self.quarantine_sessions = set()

        # Per each session, it's expiration date. This is used to control 'retained' objects from sessions in Garbage collection.
        # Must be thread-safe.
        self.session_expires_dates = dict()

        self.thread_local_data = threading.local()

    @property
    def session(self):
        return self.thread_local_data.session

    @session.setter
    def session(self, value):
        self.thread_local_data.session = value

    def is_exec_env(self):
        return True

    def get_or_new_instance_from_db(self, object_id, retry):
        """Get object from memory or database and WAIT in case we are still waiting for it to be persisted.

        Args:
            object_id: ID of object to get or create
            retry: indicates if we should retry and wait
        """
        return self.dataclay_object_loader.get_or_new_instance_from_db(object_id, retry)

    def load_object_from_db(self, instance, retry):
        """
        @postcondition: Load DataClayObject from Database
        @param instance: DataClayObject instance to fill
        @param retry: Indicates retry loading in case it is not in db.
        """
        return self.dataclay_object_loader.load_object_from_db(instance, retry)

    def get_hint(self):
        """
        @postcondition: Get hint of the current EE
        @return Hint of current EE
        """
        return settings.environment_id

    def flush_all(self):
        """
        @postcondition: Flush all objects in memory to disk.
        """
        self.dataclay_heap_manager.flush_all()

    def store_object(self, instance):
        if not instance._is_persistent:
            raise RuntimeError(
                "StoreObject should only be called on Persistent Objects. "
                "Ensure to call make_persistent first"
            )

        self.internal_store(instance, make_persistent=False)

    def make_persistent(self, instance, alias, backend_id, recursive=None):
        """This method creates a new Persistent Object using the provided stub instance and,
        if indicated, all its associated objects also Logic module API used for communication

        This function is called from a stub/execution class

        Args:
            instance (DataClayExecutionObject): Instance to make persistent
            backend_id: Indicates which is the destination backend
            recursive: Indicates if make persistent is recursive
            alias: Alias for the object

        Returns:
            ID of the backend in which te object was persisted.
        """
        del recursive
        logger.debug(f"Starting make persistent for instance {instance._object_id}")

        # It should always have a master location, since all objects intantiated
        # in a ee, get the ee as the master location
        # if not _master_ee_id:
        #     instance._master_ee_id = backend_id or self.get_backend_id_by_object_id(
        #         instance._object_id
        #     )

        if alias is not None:
            # Add a new alias to an object.
            # We call 'addAlias' with registration information in case we need to register it.
            # Use cases:
            # 1 - object was persisted without alias and not yet registered -> we need to register it with new alias.
            # 2 - object was persisted and it is already registered -> we only add a new alias
            # 3 - object was persisted with an alias and it must be already registered -> we add a new alias.
            instance._alias = alias

            if instance._is_pending_to_register:
                self.metadata_service.register_object(instance.metadata)

        return instance._master_ee_id

    def call_active_method(self, instance, method_name, parameters):
        """This method overrides parents method.
        Use to check if the instance belongs to this execution environment
        Replaces execute_implementation_aux
        """

        # TODO: Check if the object is under deserialization ¿?

        if instance._master_ee_id == settings.environment_id:
            logger.debug("Object is local")
            # get_local_instance should indeed modify the same instance instance,
            fat_instance = self.get_or_new_instance_from_db(instance._object_id, True)
            assert instance is fat_instance
            # TODO: Should i set _is_dirty always or only for getter and setter??
            return getattr(instance, method_name)(*parameters)
        else:
            logger.debug("Object is not local")
            return super().call_active_method(instance, method_name, parameters)

    #########################################
    # Helper functions, not commonruntime methods #
    #########################################

    def internal_store(self, instance, make_persistent=True):
        """Perform the storage (StoreObject call) for an instance.

        This function works for two main scenarios: the makePersistent one (in
        which the instance is not yet persistent) and the update (in which the
        instance is persistent).

        The return dictionary is the same in both cases, but note that the update
        should not use the provided instance for updating metadata to the LM.

        Args:
            instance: The DataClayObject willing to be stored.
            make_persistent: Flag, True when DS_STORE_OBJECT should be called
                and False when DS_UPSERT_OBJECT is the method to be called.
        Returns:
            A dictionary containing the classes for all stored objects.
        """
        client = self.backend_clients["@STORAGE"]

        pending_objs = [instance]
        stored_objects_classes = dict()
        serialized_objs = list()
        obj_to_register = []

        dataset_name = self.session.dataset_name

        while pending_objs:
            current_obj = pending_objs.pop()
            # Lock and make sure it is loaded
            current_obj_id = current_obj._object_id
            self.lock(current_obj_id)  # Avoid GC clean object while storing it
            try:
                if not current_obj._is_loaded:
                    current_obj = self.get_or_new_instance_from_db(current_obj_id, False)

                dcc_extradata = current_obj.get_class_extradata()
                object_id = current_obj._object_id

                if make_persistent:
                    # Ignore already persistent objects
                    if current_obj._is_persistent:
                        continue

                    obj_to_register.append(current_obj)

                # This object will soon be persistent
                current_obj._is_persistent = True
                current_obj._master_ee_id = settings.environment_id
                # Just in case (should have been loaded already)
                logger.debug(
                    "Setting loaded to true from internal store for object %s" % str(object_id)
                )
                current_obj._is_loaded = True

                logger.debug(
                    "Ready to make persistent object {%s} of class %s {%s}"
                    % (object_id, dcc_extradata.classname, dcc_extradata.class_id)
                )

                stored_objects_classes[object_id] = dcc_extradata.class_id

                # If we are not in a make_persistent, the dataset_name hint is null (?)
                serialized_objs.append(
                    SerializationLibUtilsSingleton.serialize_dcobj_with_data(
                        current_obj, pending_objs, False, None, self, False
                    )
                )
            finally:
                self.unlock(current_obj_id)

        if make_persistent:

            # TODO: It may create a lot of overhead. Better use a batch call to register
            # all objects at once. Also, it may not be necessary to even register the
            # objects at this point, since the metadata may be already registered.
            for instance in obj_to_register:
                self.metadata_service.register_object(instance.metadata)

            client.ds_store_objects(
                self.session.id,
                serialized_objs,
                False,
                None,
            )
        else:
            client.ds_upsert_objects(self.session.id, serialized_objs)

    def get_operation_info(self, object_id, operation_name):
        dcc_extradata = self.get_object_by_id(object_id).get_class_extradata()
        metaclass_container = dcc_extradata.metaclass_container
        operation = metaclass_container.get_operation_from_name(operation_name)
        return operation

    def get_implementation_id(self, object_id, operation_name, implementation_idx=0):
        operation = self.get_operation_info(object_id, operation_name)
        return operation.implementations[0].dataClayID

    def check_and_fill_volatile_under_deserialization(self, volatile_obj, ifacebitmaps):
        """Check if there is a volatile object with ID provided pending to deserialize and if so, deserialize it since it is needed.
        :param volatile_obj: object to check
        :param ifacebitmaps: Interface bitmaps for deserialization
        :returns: true if it was filled and volatile, false otherwise
        :type volatile_obj: DataClayObject
        :type ifacebitmaps: dict
        :rtype: boolean
        """

        object_id = volatile_obj._object_id
        if hasattr(self.thread_local_data, "volatiles_under_deserialization"):
            if self.thread_local_data.volatiles_under_deserialization is not None:
                for obj_with_data in self.thread_local_data.volatiles_under_deserialization:
                    curr_obj_id = obj_with_data.object_id
                    if object_id == curr_obj_id:
                        if hasattr(volatile_obj, "__setstate__"):
                            # Return true like the object is already deserialized, this will allow
                            # any volatile under deserialization with __setstate__ to be actually deserialized
                            # TODO: check race conditions
                            return True
                        # deserialize it
                        metaclass_id = volatile_obj.get_class_extradata().class_id
                        hint = volatile_obj._master_ee_id
                        self.get_or_new_volatile_instance_and_load(
                            object_id, metaclass_id, hint, obj_with_data, ifacebitmaps
                        )
                        return True
        return False

    def add_session_reference(self, object_id):
        """
        @summary Add +1 reference associated to thread session
        @param object_id ID of object.
        """
        session_id = self.session.id
        if session_id is None:
            # session id can be none in case of when federated
            return

        if object_id not in self.references_hold_by_sessions:
            """race condition: two objects creating set of sessions at same time"""
            self.lock(object_id)
            try:
                if object_id not in self.references_hold_by_sessions:
                    session_refs = set()
                    self.references_hold_by_sessions[object_id] = session_refs
            finally:
                self.unlock(object_id)
        else:
            session_refs = self.references_hold_by_sessions.get(object_id)
        session_refs.add(session_id)

        """ add expiration date of session if not present
        IMPORTANT: if CHECK_SESSION=FALSE then we use a default expiration date for all sessions
        In this case, sessions must be explicitly closed otherwise GC is never going to clean unused objects from sessions.
        Concurrency note: adding two times same expiration date is not a problem since exp. date is the same. We avoid locking.
        """
        if not session_id in self.session_expires_dates:
            if Configuration.CHECK_SESSION:
                """TODO: implement session control in python"""
            else:
                expiration_date = Configuration.NOCHECK_SESSION_EXPIRATION

            """
            // === concurrency note === //
            T1 is here, before put. This is a session that was already used and was restarted.
            T2 is in @getReferenceCounting and wants to remove session since it expired.
            What if T2 removes it after the put?
            Synchronization is needed to avoid this. It is not a big penalty if session expiration date was already added.
            """
            self.lock(session_id)  # Use same locking system for object ids.
            try:
                self.session_expires_dates[session_id] = expiration_date
            finally:
                self.unlock(session_id)

    def delete_alias(self, instance):
        alias = instance._alias
        if alias is not None:
            self.delete_alias_in_dataclay(alias, instance._dataset_name)
        instance._alias = None
        instance._is_dirty = True

    def close_session_in_ee(self, session_id):
        """Close session in EE. Subtract session references for GC."""

        logger.debug(f"[==DGC==] Closing session {session_id}")

        """ Closing session means set expiration date to now """
        self.session_expires_dates[session_id] = datetime.datetime.now()

    def get_retained_references(self):
        """
        @summary Get retained refs by this EE
        @return Retained refs (alias, sessions, ...)
        """
        retained_refs = set()

        """ memory references """
        for oid in self.dataclay_heap_manager.get_object_ids_retained():
            retained_refs.add(oid)
        logger.debug("[==GC==] Session refs: %s" % str(len(self.references_hold_by_sessions)))
        logger.debug(
            "References hold by sessions: %s" % str(self.references_hold_by_sessions.keys())
        )

        """ session references """
        now = datetime.datetime.now()

        sessions_to_close = set()
        for oid in list(
            self.references_hold_by_sessions.keys()
        ):  # use keys as copy to avoid concurrency problems
            sessions_of_obj = self.references_hold_by_sessions.get(oid)
            """ create a copy of the list to avoid modification issues while iterating and concurrence problems """
            for cur_session in list(sessions_of_obj):

                """check session expired"""
                session_expired = False
                expired_date = self.session_expires_dates.get(cur_session)
                if expired_date is not None and now > expired_date:
                    if cur_session in self.quarantine_sessions:
                        # Session is actually removed
                        session_expired = True

                        """ check again expiration date to see if it is expired. If expired, remove. """
                        cur_expired_date = self.session_expires_dates.get(cur_session)
                        if cur_expired_date is not None and now > cur_expired_date:
                            """
                            do not remove expiration date from session till there is no objects in that session
                            add it to sessions to close after all processing"""
                            sessions_to_close.add(cur_session)

                    else:
                        self.quarantine_sessions.add(cur_session)
                elif expired_date is not None and now < expired_date:
                    # check if session was in quarantine: if so, remove it from there (session restart)
                    if cur_session in self.quarantine_sessions:
                        self.quarantine_sessions.remove(cur_session)

                if session_expired:
                    """close session"""
                    sessions_of_obj.remove(cur_session)

                    """
                    // === concurrency note === //
                    when should we remove an entry in the references_hold_by_sessions map?
                    1 - when no session is using the object
                    2 - when object is not in memory
                    so, we check both here and we remove it if needed:
                    TODO: what if after if, it is added?
                    """
                    logger.debug("Session %s expired" % str(cur_session))
                    if len(sessions_of_obj) == 0:
                        logger.debug("Removing session reference for oid %s" % str(oid))
                        del self.references_hold_by_sessions[oid]

                else:
                    retained_refs.add(oid)

        """ check closed sessions """
        """ Remove all expired sessions if, and only if, there is no object retained by it. 
        TODO: improve this implementation."""
        for session_to_close in sessions_to_close:
            obj_using_session = False
            for sessions_of_obj in self.references_hold_by_sessions.values():
                if session_to_close in sessions_of_obj:
                    obj_using_session = True
                    break

            if not obj_using_session:
                del self.session_expires_dates[session_to_close]

        return retained_refs

    def get_from_sl(self, object_id):
        """Get from SL associated to this EE.
        :param object_id: id of the object to get
        :type object_id: ObjectID
        :returns: Bytes of object
        :rtype: Byte array
        """
        return self.backend_clients["@STORAGE"].get_from_db(settings.environment_id, object_id)

    def update_to_sl(self, object_id, obj_bytes, dirty):
        """Update to SL associated to this EE.
        :param object_id: id of the object
        :param obj_bytes: bytes to update
        :param dirty: indicates if object is dirty or not
        :returns: None
        :type object_id: ObjectID
        :type obj_bytes: Byte array
        :type dirty: Boolean
        :rtype: None
        """
        return self.backend_clients["@STORAGE"].update_to_db(
            settings.environment_id, object_id, obj_bytes, dirty
        )

    def synchronize(self, instance, operation_name, params):
        session_id = self.session.id
        object_id = instance._object_id
        operation = self.get_operation_info(instance._object_id, operation_name)
        implementation_id = self.get_implementation_id(instance._object_id, operation_name)
        # === SERIALIZE PARAMETERS ===
        serialized_params = SerializationLibUtilsSingleton.serialize_params_or_return(
            params=[params],
            iface_bitmaps=None,
            params_spec=operation.params,
            params_order=operation.paramsOrder,
            hint_volatiles=instance._master_ee_id,
            runtime=self,
        )
        self.execution_environment.synchronize(
            session_id, object_id, implementation_id, serialized_params
        )

    def detach_object_from_session(self, object_id, _):
        cur_session = self.session.id
        if object_id in self.references_hold_by_sessions:
            sessions_of_obj = self.references_hold_by_sessions.get(object_id)
            if cur_session in sessions_of_obj:
                sessions_of_obj.remove(cur_session)
                logger.debug(
                    "Session %s removed from object %s" % (str(cur_session), str(object_id))
                )
                if len(sessions_of_obj) == 0:
                    del self.references_hold_by_sessions[object_id]

    def federate_to_backend(self, dc_obj, external_execution_environment_id, recursive):
        object_id = dc_obj._object_id
        session_id = self.session.id
        logger.debug(
            "[==FederateObject==] Starting federation of object by %s with dest dataClay %s, and session %s",
            object_id,
            external_execution_environment_id,
            session_id,
        )
        self.execution_environment.federate(
            session_id, object_id, external_execution_environment_id, recursive
        )

    def unfederate_from_backend(self, dc_obj, external_execution_environment_id, recursive):
        object_id = dc_obj._object_id
        session_id = self.session.id
        logger.debug(
            "[==UnfederateObject==] Starting unfederation of object %s with ext backend %s, and session %s",
            object_id,
            external_execution_environment_id,
            session_id,
        )
        self.execution_environment.unfederate(
            session_id, object_id, external_execution_environment_id, recursive
        )
