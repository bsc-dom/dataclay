""" BackendRuntime """
from __future__ import annotations

import datetime
import logging
import pickle
import threading
from typing import TYPE_CHECKING

from dataclay.backend.data_manager import DataManager
from dataclay.config import settings
from dataclay.exceptions import *
from dataclay.metadata.api import MetadataAPI
from dataclay.runtime import LockManager
from dataclay.runtime.runtime import DataClayRuntime
from dataclay.utils import metrics

if TYPE_CHECKING:
    from uuid import UUID

    from dataclay.dataclay_object import DataClayObject
    from dataclay.metadata.kvdata import Session

logger = logging.getLogger(__name__)


class BackendRuntime(DataClayRuntime):
    data_manager: DataManager = None
    thread_local_data: threading.local

    def __init__(self, kv_host: str, kv_port: int, backend_id: UUID):
        # Initialize parent
        metadata_service = MetadataAPI(kv_host, kv_port)
        super().__init__(metadata_service, backend_id)

        self.data_manager = DataManager()
        # start heap manager. Invokes run() in a separate thread
        self.data_manager.start()

        # References hold by sessions. Resource note: Maximum size of this map is maximum number of objects allowed in EE x sessions.
        # Also, important to think what happens if one single session is associated to two client threads? use case?
        # should we allow that?
        # Must be thread-safe.
        self.references_hold_by_sessions = {}

        # Sessions in quarantine. note: maximum size of this map is max number of sessions per EE: This map is needed to solve a race
        # condition in Global Garbage collection (@see getReferenceCounting).
        self.quarantine_sessions = set()

        # Per each session, it's expiration date. This is used to control 'retained' objects from sessions in Garbage collection.
        # Must be thread-safe.
        self.session_expires_dates = {}

        self.thread_local_data = threading.local()

    @property
    def session(self) -> Session:
        return self.thread_local_data.session

    @session.setter
    def session(self, value: Session):
        self.thread_local_data.session = value

    def set_session_by_id(self, session_id: UUID):
        session = self.metadata_service.get_session(session_id)
        self.session = session

    # Shutdown

    def stop(self):
        # Remove backend entry from metadata
        self.metadata_service.delete_backend(settings.backend.id)

        # Stop DataManager
        logger.debug("Stopping DataManager")
        self.data_manager.shutdown()
        self.data_manager.join()
        logger.debug("DataManager stopped.")

        self.close_backend_clients()
        self.data_manager.flush_all()

    # Garbage collector

    def add_session_reference(self, object_id):
        """
        @summary Add +1 reference associated to thread session
        @param object_id ID of object.
        """
        raise Exception("To refactor")

        session_id = self.session.id
        if session_id is None:
            # session id can be none in case of when federated
            return

        if object_id not in self.references_hold_by_sessions:
            """race condition: two objects creating set of sessions at same time"""
            with LockManager.write(object_id):
                if object_id not in self.references_hold_by_sessions:
                    session_refs = set()
                    self.references_hold_by_sessions[object_id] = session_refs
        else:
            session_refs = self.references_hold_by_sessions.get(object_id)
        session_refs.add(session_id)

        """ add expiration date of session if not present
        IMPORTANT: if CHECK_SESSION=FALSE then we use a default expiration date for all sessions
        In this case, sessions must be explicitly closed otherwise GC is never going to clean unused objects from sessions.
        Concurrency note: adding two times same expiration date is not a problem since exp. date is the same. We avoid locking.
        """
        if not session_id in self.session_expires_dates:
            if settings.check_session:
                """TODO: implement session control in python"""
            else:
                expiration_date = settings.nocheck_session_expiration

            """
            // === concurrency note === //
            T1 is here, before put. This is a session that was already used and was restarted.
            T2 is in @getReferenceCounting and wants to remove session since it expired.
            What if T2 removes it after the put?
            Synchronization is needed to avoid this. It is not a big penalty if session expiration date was already added.
            """
            with LockManager.write(session_id):
                self.session_expires_dates[session_id] = expiration_date

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

    def get_retained_references(self):
        """
        @summary Get retained refs by this EE
        @return Retained refs (alias, sessions, ...)
        """
        raise Exception("To refactor")

        retained_refs = set()

        """ memory references """
        for oid in self.data_manager.keys():
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

    # Replicas

    def synchronize(self, instance, operation_name, params):
        raise Exception("To refactor")
        session_id = self.session.id
        object_id = instance._dc_meta.id
        operation = self.get_operation_info(instance._dc_meta.id, operation_name)
        implementation_id = self.get_implementation_id(instance._dc_meta.id, operation_name)
        # === SERIALIZE PARAMETERS ===
        serialized_params = SerializationLibUtilsSingleton.serialize_params_or_return(
            params=[params],
            iface_bitmaps=None,
            params_spec=operation.params,
            params_order=operation.paramsOrder,
            hint_volatiles=instance._dc_meta.master_backend_id,
            runtime=self,
        )
        self.execution_environment.synchronize(
            session_id, object_id, implementation_id, serialized_params
        )

    # Federations

    def federate_to_backend(self, dc_obj, external_execution_environment_id, recursive):
        raise Exception("To refactor")
        object_id = dc_obj._dc_meta.id
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
        raise Exception("To refactor")
        object_id = dc_obj._dc_meta.id
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
