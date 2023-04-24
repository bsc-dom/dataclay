""" Class description goes here. """

from __future__ import annotations

import io
import logging
import pickle
import time
import traceback
import uuid
from typing import TYPE_CHECKING

from dataclay import utils
from dataclay.backend.client import BackendClient
from dataclay.backend.runtime import BackendRuntime
from dataclay.conf import settings
from dataclay.exceptions import *
from dataclay.runtime import UUIDLock, set_runtime
from dataclay.utils.pickle import RecursiveLocalPickler, RecursiveLocalUnpickler
from dataclay.utils.tracing import trace

if TYPE_CHECKING:
    from dataclay.dataclay_object import DataClayObject


logging.basicConfig(level=logging.DEBUG)
tracer = trace.get_tracer(__name__)
logger = utils.LoggerEvent(logging.getLogger(__name__))


class BackendAPI:
    def __init__(self, name, port, kv_host, kv_port):
        # NOTE: the port is (atm) exclusively for unique identification of an EE
        # (given that the name is shared between all EE that share a SL, which happens in HPC deployments)
        self.name = name
        self.port = port

        # Initialize runtime
        self.runtime = BackendRuntime(kv_host, kv_port)
        set_runtime(self.runtime)

        # UNDONE: Do not store EE information. If restarted, create new EE uuid.
        self.backend_id = settings.DATACLAY_BACKEND_ID
        logger.info(f"Initialized Backend with ID: {self.backend_id}")

    def is_ready(self, timeout=None, pause=0.5):
        ref = time.time()
        now = ref
        if self.runtime.metadata_service.is_ready(timeout):
            # Check that dataclay_id is defined. If it is not defined, it could break things
            while timeout is None or (now - ref) < timeout:
                try:
                    dataclay_id = self.runtime.metadata_service.get_dataclay("this").id
                    settings.DATACLAY_ID = dataclay_id
                    return True
                except DoesNotExistError:
                    time.sleep(pause)
                    now = time.time()

        return False

    def exists(self, object_id):
        with UUIDLock(object_id):
            # object might be in heap but as a "proxy"
            # since this function is used from SL after checking if the object is in database,
            # we return false if the object is not loaded so the combination of SL exists and EE exists
            # can tell if the object actually exists
            # summary: the object only exist in EE if it is loaded.
            try:
                return self.runtime.inmemory_objects[object_id]._dc_is_loaded
            except KeyError:
                return False

    # Object Methods

    def make_persistent(self, serialized_dicts: list[bytes]):
        unserialized_objects = dict()
        for serial_dict in serialized_dicts:
            object_dict = RecursiveLocalUnpickler(
                io.BytesIO(serial_dict), unserialized_objects
            ).load()
            object_id = object_dict["_dc_id"]

            try:
                proxy_object = unserialized_objects[object_id]
            except KeyError:
                cls: type[DataClayObject] = object_dict["_dc_class"]
                proxy_object = cls.new_proxy_object()
                unserialized_objects[object_id] = proxy_object

            vars(proxy_object).update(object_dict)
            proxy_object._dc_is_local = True
            proxy_object._dc_is_loaded = True
            proxy_object._dc_backend_id = self.backend_id

        assert len(serialized_dicts) == len(unserialized_objects)

        for object_id, proxy_object in unserialized_objects.items():
            self.runtime.inmemory_objects[object_id] = proxy_object
            self.runtime.heap_manager.retain_in_heap(proxy_object)

            self.runtime.metadata_service.register_object(proxy_object.metadata)
            proxy_object._dc_is_registered = True

    def call_active_method(self, session_id, object_id, method_name, args, kwargs):
        # NOTE: Session (dataset) is needed for make_persistents inside dc_methods.
        self.runtime.set_session_by_id(session_id)
        instance = self.runtime.get_object_by_id(object_id)

        # NOTE: When the object is not local, a custom exception is sent
        # for the client to update the backend_id, and call_active_method again
        if not instance._dc_is_local:
            logger.warning(
                f"Object {object_id} with wrong backend_id. Update to {instance._dc_backend_id}"
            )
            # NOTE: We check to the metadata because when consolidating an object
            # it might be that the proxy is pointing to the wrong backend_id which is
            # the same current backend, creating a infinite loop. This could be solve also
            # by passing the backend_id of the new object to the proxy, but this can create
            # problems with race conditions (e.g. a move before the consolidation). Therefore,
            # we check to the metadata which is more reliable.
            object_md = self.runtime.metadata_service.get_object_md_by_id(object_id)
            instance._dc_backend_id = object_md.backend_id
            return pickle.dumps(ObjectWithWrongBackendId(instance._dc_backend_id)), False

        args = pickle.loads(args)
        kwargs = pickle.loads(kwargs)

        try:
            value = getattr(instance, method_name)(*args, **kwargs)
            if value is not None:
                value = pickle.dumps(value)
            return value, False
        except Exception as e:
            return pickle.dumps(e), True

    # Store Methods

    def get_object_properties(self, object_id, recursive):
        """Returns a non-persistent copy of the object with ID provided

        Args:
            object_id: ID of the object
        Returns:
            the generated non-persistent objects
        """
        # TODO: Implement recursive option
        instance = self.runtime.get_object_by_id(object_id)

        # Lock to avoid unloading after the object is loaded
        with UUIDLock(object_id):
            # NOTE: The object should be loaded to get the _dc_properties
            # TODO: Maybe send directly the pickled file if not loaded?
            self.runtime.load_object_from_db(instance)
            serialized_properties = pickle.dumps(instance._dc_properties)

        return serialized_properties

    def update_object(self, object_id, serialized_properties):
        """Updates an object with ID provided with contents from another object"""
        instance = self.runtime.get_object_by_id(object_id)
        object_properties = pickle.loads(serialized_properties)

        with UUIDLock(object_id):
            self.runtime.load_object_from_db(instance)
            vars(instance).update(object_properties)

    def proxify_object(self, object_id, new_object_id):
        instance = self.runtime.get_object_by_id(object_id)

        with UUIDLock(object_id):
            self.runtime.load_object_from_db(instance)
            instance._clean_dc_properties()
            instance._dc_is_loaded = False
            instance._dc_is_local = False
            self.runtime.heap_manager.release_from_heap(instance)

            # NOTE: There is no need to delete, and it may be good
            # in case that an object was serialized to disk before a
            # consolidation. However, it will be deleted also since
            # inmemory_objects is a weakref dict.
            # del self.runtime.inmemory_objects[object_id]
            self.runtime.metadata_service.delete_object(object_id)
            instance._dc_id = new_object_id

    def change_object_id(self, object_id, new_object_id):
        instance = self.runtime.get_object_by_id(object_id)

        with UUIDLock(object_id):
            self.runtime.load_object_from_db(instance)

            # We need to update the loaded_objects with the new object_id key
            self.runtime.heap_manager.release_from_heap(instance)

            instance._dc_id = new_object_id
            self.runtime.heap_manager.retain_in_heap(instance)

            # Also update the inmemory_objects with the new object_id key
            self.runtime.inmemory_objects[new_object_id] = self.runtime.inmemory_objects[object_id]
            del self.runtime.inmemory_objects[object_id]

            self.runtime.metadata_service.change_object_id(object_id, new_object_id)

    def move_object(self, object_id, backend_id, recursive):
        # TODO: check that the object is local to us
        instance = self.runtime.get_object_by_id(object_id)

        with UUIDLock(object_id):
            # NOTE: The object should be loaded to get the _dc_properties
            # TODO: Maybe send directly the pickled file if not loaded?

            # Option 1
            # self.runtime.heap_manager.unload_object(object_id)
            # path = f"{settings.STORAGE_PATH}/{object_id}"
            # with open(path, "rb") as file:
            #     serialized_properties = file.read()

            # Option 2
            self.runtime.load_object_from_db(instance)

            f = io.BytesIO()
            serialized_local_dicts = []
            visited_objects = {instance._dc_id: instance}

            RecursiveLocalPickler(f, visited_objects, serialized_local_dicts, recursive).dump(
                instance._dc_dict
            )
            serialized_local_dicts.append(f.getvalue())
            backend_client = self.runtime.get_backend_client(backend_id)
            backend_client.make_persistent(serialized_local_dicts)

            # TODO: Remove pickle file to reduce space

            for dc_object in visited_objects.values():
                self.runtime.heap_manager.release_from_heap(dc_object)
                dc_object._clean_dc_properties()
                dc_object._dc_is_local = False
                dc_object._dc_is_loaded = False
                dc_object._dc_backend_id = backend_id

    # Shutdown

    def shutdown(self):
        self.runtime.stop()

    def flush_all(self):
        self.runtime.heap_manager.flush_all()

    def move_all_objects(self):
        dc_objects = self.runtime.metadata_service.get_all_objects()
        self.runtime.update_backend_clients()
        backends = self.runtime.backend_clients

        if len(backends) <= 1:
            raise DataClayException("No other backend to drain to. Abort!")

        num_objects = len(dc_objects)
        mean = -(num_objects // -(len(backends) - 1))

        backends_objects = {backend_id: [] for backend_id in backends.keys()}
        for object_md in dc_objects.values():
            backends_objects[object_md.backend_id].append(object_md.id)

        backends_diff = dict()
        for backend_id, objects in backends_objects.items():
            diff = len(objects) - mean
            backends_diff[backend_id] = diff

        # for backend_id, object_ids in backends_objects.items():
        #     if backends_diff[backend_id] <= 0:
        #         continue

        object_ids = backends_objects[self.backend_id]

        for new_backend_id in backends_objects.keys():
            if new_backend_id == self.backend_id or backends_diff[new_backend_id] >= 0:
                continue
            while backends_diff[new_backend_id] < 0:
                object_id = object_ids.pop()
                self.move_object(object_id, new_backend_id, None)
                backends_diff[new_backend_id] += 1

    # Replicas

    def new_replica(self, session_id, object_id, dest_backend_id, recursive):
        """Creates a new replica of the object with ID provided in the backend specified.

        Args:
            session_id: ID of session
            object_id: ID of the object
            dest_backend_id: destination backend id
            recursive: Indicates if all sub-objects must be replicated as well.
        """
        logger.debug("----> Starting new replica of %s to backend %s", object_id, dest_backend_id)

        serialized_objs = self.get_objects(
            session_id, {object_id}, set(), recursive, dest_backend_id, 1
        )
        client_backend = self.runtime.get_backend_client(dest_backend_id)
        client_backend.ds_store_objects(session_id, serialized_objs, False, None)
        replicated_ids = set()
        for serialized_obj in serialized_objs:
            replicated_ids.add(serialized_obj.object_id)
        logger.debug("<---- Finished new replica of %s", object_id)
        return replicated_ids

    def synchronize(
        self, session_id, object_id, implementation_id, serialized_value, calling_backend_id=None
    ):
        # set field
        logger.debug(
            f"----> Starting synchronization of {object_id} from calling backend {calling_backend_id}"
        )

        self.ds_exec_impl(object_id, implementation_id, serialized_value, session_id)
        instance = self.get_local_instance(object_id, True)
        src_exec_env_id = instance._dc_backend_id()
        if src_exec_env_id is not None:
            logger.debug(f"Found origin location {src_exec_env_id}")
            if calling_backend_id is None or src_exec_env_id != calling_backend_id:
                # do not synchronize to calling source (avoid infinite loops)
                dest_backend = self.runtime.get_backend_client(src_exec_env_id)
                logger.debug(
                    f"----> Propagating synchronization of {object_id} to origin location {src_exec_env_id}"
                )

                dest_backend.synchronize(
                    session_id,
                    object_id,
                    implementation_id,
                    serialized_value,
                    calling_backend_id=self.backend_id,
                )

        replica_locations = instance._dc_replica_backend_ids
        if replica_locations is not None:
            logger.debug(f"Found replica locations {replica_locations}")
            for replica_location in replica_locations:
                if calling_backend_id is None or replica_location != calling_backend_id:
                    # do not synchronize to calling source (avoid infinite loops)
                    dest_backend = self.runtime.get_backend_client(replica_location)
                    logger.debug(
                        f"----> Propagating synchronization of {object_id} to replica location {replica_location}"
                    )
                    dest_backend.synchronize(
                        session_id,
                        object_id,
                        implementation_id,
                        serialized_value,
                        calling_backend_id=self.backend_id,
                    )
        logger.debug(f"----> Finished synchronization of {object_id}")

    # Federation

    def federate(self, session_id, object_id, external_execution_env_id, recursive):
        """Federate object with id provided to external execution env id specified

        Args:
            session_id: id of the session federating objects
            object_id: id of object to federate
            external_execution_id: id of dest external execution environment
            recursive: indicates if federation is recursive
        """
        logger.debug("----> Starting federation of %s", object_id)

        object_ids = set()
        object_ids.add(object_id)
        # TODO: check that current dataClay/EE has permission to federate the object (refederation use-case)
        serialized_objs = self.get_objects(
            session_id, object_ids, set(), recursive, external_execution_env_id, 1
        )
        client_backend = self.runtime.get_backend_client(external_execution_env_id)
        client_backend.notify_federation(session_id, serialized_objs)
        # TODO: add federation reference to object send ?? how is it working with replicas?
        logger.debug("<---- Finished federation of %s", object_id)

    def notify_federation(self, session_id, objects_to_persist):
        """This function will deserialize object "parameters" (i.e. object to persist
        and subobjects if needed) into dataClay memory heap using the same design as for
        volatile parameters. This function processes objects recieved from federation calls.

        Args:
            session_id: ID of session of federation call
            objects_to_persist: [num_params, imm_objs, lang_objs, vol_params, pers_params]
        """

        self.set_local_session(session_id)

        try:
            logger.debug("----> Notified federation")

            # No need to provide params specs or param order since objects are not language types
            federated_objs = self.store_in_memory(objects_to_persist)

            # Register objects with alias (should we?)
            for object in federated_objs:
                if object._dc_alias:
                    self.runtime.metadata_service.register_object(object.metadata)

            for federated_obj in federated_objs:
                try:
                    federated_obj.when_federated()
                except Exception:
                    # ignore if method is not implemented
                    pass

        except Exception as e:
            traceback.print_exc()
            raise e
        logger.debug("<---- Finished notification of federation")

    def unfederate(self, session_id, object_id, external_execution_env_id, recursive):
        """Unfederate object in external execution environment specified

        Args:
            session_id: id of session
            object_id: id of the object
            external_execution_env_id: external ee
            recursive: also unfederates sub-objects
        """
        # TODO: redirect unfederation to owner if current dataClay is not the owner, check origLoc belongs to current dataClay
        try:
            logger.debug("----> Starting unfederation of %s", object_id)
            object_ids = set()
            object_ids.add(object_id)
            serialized_objs = self.get_objects(
                session_id, object_ids, set(), recursive, external_execution_env_id, 2
            )

            unfederate_per_backend = dict()

            for serialized_obj in serialized_objs:
                replica_locs = serialized_obj.metadata.replica_locations
                for replica_loc in replica_locs:
                    exec_env = self.runtime.get_execution_environment_info(replica_loc)
                    if exec_env.dataclay_instance_id != self.runtime.dataclay_id:
                        if (
                            external_execution_env_id is not None
                            and replica_loc != external_execution_env_id
                        ):
                            continue
                        objs_in_backend = None
                        if replica_loc not in unfederate_per_backend:
                            objs_in_backend = set()
                            unfederate_per_backend[replica_loc] = objs_in_backend
                        else:
                            objs_in_backend = unfederate_per_backend[replica_loc]
                        objs_in_backend.add(serialized_obj.object_id)

            for external_ee_id, objs_in_backend in unfederate_per_backend.items():
                client_backend = self.runtime.get_backend_client(external_ee_id)
                client_backend.notify_unfederation(session_id, objs_in_backend)

            logger.debug("<---- Finished unfederation of %s", object_ids)

        except Exception as e:
            traceback.print_exc()
            raise e

    def notify_unfederation(self, session_id, object_ids):
        """This function is called when objects are unfederated.

        Args:
            session_id: ID of session of federation call
            object_ids: List of IDs of the objects to unfederate
        """
        self.set_local_session(session_id)
        logger.debug("---> Notified unfederation: running when_unfederated")
        try:
            for object_id in object_ids:
                instance = self.get_local_instance(object_id, True)

                try:
                    instance.when_unfederated()
                except:
                    # ignore if method is not implemented
                    pass
                instance.set_origin_location(None)
                try:
                    if instance._dc_alias is not None and instance._dc_alias != "":
                        logger.debug(f"Removing alias {instance._dc_alias}")
                        self.self.runtime.delete_alias(instance)

                except Exception as ex:
                    traceback.print_exc()
                    logger.debug(
                        f"Caught exception {type(ex).__name__}, Ignoring if object was not registered yet"
                    )
                    # ignore if object was not registered yet
                    pass
        except DataClayException as e:
            # TODO: better algorithm to avoid unfederation in wrong backend
            logger.debug(
                f"Caught exception {type(e).__name__}, Ignoring if object is not in current backend"
            )
        except Exception as e:
            logger.debug(f"Caught exception {type(e).__name__}")
            raise e
        logger.debug("<--- Finished notification of unfederation")

    # Update Object

    def get_objects(
        self,
        session_id,
        object_ids,
        already_obtained_objs,
        recursive,
        dest_replica_backend_id=None,
        update_replica_locs=0,
    ):
        """Get the serialized objects with id provided

        Args:
            session_id: ID of session
            object_ids: IDs of the objects to get
            recursive: Indicates if, per each object to get, also obtain its associated objects.
            dest_replica_backend_id:
                Destination backend of objects being obtained for replica or NULL if going to client
            update_replica_locs:
                If 1, provided replica dest backend id must be added to replica locs of obtained objects
                If 2, provided replica dest backend id must be removed from replica locs
                If 0, replicaDestBackendID field is ignored
        Returns:
            List of serialized objects
        """
        logger.debug("[==Get==] Getting objects %s", object_ids)

        self.set_local_session(session_id)

        result = list()
        pending_oids_and_hint = list()
        objects_in_other_backend = list()

        for oid in object_ids:
            if recursive:
                # Add object to pending
                pending_oids_and_hint.append([oid, None])
                while pending_oids_and_hint:
                    current_oid_and_hint = pending_oids_and_hint.pop()
                    current_oid = current_oid_and_hint[0]
                    current_hint = current_oid_and_hint[1]
                    if current_oid in already_obtained_objs:
                        # Already Read
                        logger.debug("[==Get==] Object %s already read", current_oid)
                        continue
                    if current_hint is not None and current_hint != self.backend_id:
                        # in another backend
                        objects_in_other_backend.append([current_oid, current_hint])
                        continue

                    else:
                        try:
                            logger.debug(
                                "[==Get==] Trying to get local instance for object %s", current_oid
                            )
                            obj_with_data = self.get_object_internal(
                                current_oid, dest_replica_backend_id, update_replica_locs
                            )
                            if obj_with_data is not None:
                                result.append(obj_with_data)
                                already_obtained_objs.add(current_oid)
                                # Get associated objects and add them to pendings
                                obj_metadata = obj_with_data.metadata
                                for tag in obj_metadata.tags_to_oids:
                                    oid_found = obj_metadata.tags_to_oids[tag]
                                    hint_found = obj_metadata.tags_to_hints[tag]
                                    if (
                                        oid_found != current_oid
                                        and oid_found not in already_obtained_objs
                                    ):
                                        pending_oids_and_hint.append([oid_found, hint_found])

                        except:
                            traceback.print_exc()
                            logger.debug(
                                f"[==Get==] Not in this backend (wrong or null hint) for {current_oid}"
                            )
                            # Get in other backend (remove hint, it failed here)
                            objects_in_other_backend.append([current_oid, None])
            else:
                try:
                    obj_with_data = self.get_object_internal(
                        oid, dest_replica_backend_id, update_replica_locs
                    )
                    if obj_with_data is not None:
                        result.append(obj_with_data)
                except:
                    logger.debug("[==Get==] Object is in other backend")
                    # Get in other backend
                    objects_in_other_backend.append([oid, None])

        obj_with_data_in_other_backends = self.get_objects_in_other_backends(
            session_id,
            objects_in_other_backend,
            already_obtained_objs,
            recursive,
            dest_replica_backend_id,
            update_replica_locs,
        )

        for obj_in_oth_back in obj_with_data_in_other_backends:
            result.append(obj_in_oth_back)
        logger.debug("[==Get==] Finished get objects len = %s", str(len(result)))
        return result

    def get_object_internal(self, oid, dest_replica_backend_id, update_replica_locs):
        """Get object internal function

        Args:
            oid: ID of the object ot get
            dest_replica_backend_id:
                Destination backend of objects being obtained for replica or NULL if going to client
            update_replica_locs:
                If 1, provided replica dest backend id must be added to replica locs of obtained objects
                If 2, provided replica dest backend id must be removed from replica locs
                If 0, replicaDestBackendID field is ignored
        Returns:
            Object with data
        """
        # Serialize the object
        logger.debug("[==GetInternal==] Trying to get local instance for object %s", oid)

        # ToDo: Manage better this try/catch
        # Race condition with gc: make sure GC does not CLEAN the object while retrieving/serializing it!
        with UUIDLock(oid):
            current_obj = self.get_local_instance(oid, False)
            pending_objs = list()

            # update_replica_locs = 1 means new replica/federation
            if dest_replica_backend_id is not None and update_replica_locs == 1:
                if current_obj._dc_replica_backend_ids is not None:
                    if dest_replica_backend_id in current_obj._dc_replica_backend_ids:
                        # already replicated
                        logger.debug(f"WARNING: Found already replicated object {oid}. Skipping")
                        return None

            # Add object to result and obtained_objs for return and recursive
            obj_with_data = SerializationLibUtilsSingleton.serialize_dcobj_with_data(
                current_obj, pending_objs, False, current_obj._dc_backend_id, self.runtime, False
            )

            if dest_replica_backend_id is not None and update_replica_locs == 1:
                current_obj._add_replica_location(dest_replica_backend_id)
                current_obj._dc_is_dirty = True
                obj_with_data.metadata.origin_location = self.backend_id
            elif update_replica_locs == 2:
                if dest_replica_backend_id is not None:
                    current_obj._remove_replica_location(dest_replica_backend_id)
                else:
                    current_obj._clear_replica_locations()
                current_obj._dc_is_dirty = True

        return obj_with_data

    def get_objects_in_other_backends(
        self,
        session_id,
        objects_in_other_backend,
        already_obtained_objs,
        recursive,
        dest_replica_backend_id,
        update_replica_locs,
    ):
        """Get object in another backend. This function is called from DbHandler in a recursive get.

        Args:
            session_id: ID of session
            objects_in_other_backend: List of metadata of objects to read. It is useful to avoid multiple trips.
            recursive: Indicates is recursive
            dest_replica_backend_id:
                Destination backend of objects being obtained for replica or NULL if going to client
            update_replica_locs:
                If 1, provided replica dest backend id must be added to replica locs of obtained objects
                If 2, provided replica dest backend id must be removed from replica locs
                If 0, replicaDestBackendID field is ignored
        Returns:
            List of serialized objects
        """
        raise Exception("To refactor")
        result = list()

        # Prepare to unify calls (only one call for DS)
        objects_per_backend = dict()

        for curr_oid_and_hint in objects_in_other_backend:
            object_id = curr_oid_and_hint[0]
            hint = curr_oid_and_hint[1]

            if hint is None:
                logger.debug(f"[==GetObjectsInOtherBackend==] Looking for metadata of {object_id}")
                object_md = self.get_object_metadata(object_id)
                hint = object_md.backend_id
            try:
                objects_in_backend = objects_per_backend[hint]
            except KeyError:
                objects_in_backend = set()
                objects_per_backend[hint] = objects_in_backend
            objects_in_backend.add(object_id)

        # Now Call
        for backend_id, objects_to_get in objects_per_backend.items():
            if dest_replica_backend_id is None or dest_replica_backend_id != backend_id:
                logger.debug(
                    "[==GetObjectsInOtherBackend==] Get from other location, objects: %s",
                    objects_to_get,
                )
                backend = self.runtime.ee_infos[backend_id]
                try:
                    client_backend = self.runtime.backend_clients[backend_id]
                except KeyError:
                    logger.debug(
                        "[==GetObjectsInOtherBackend==] Not found Client to ExecutionEnvironment {%s}!"
                        " Starting it at %s:%d",
                        backend_id,
                        backend.hostname,
                        backend.port,
                    )

                    client_backend = BackendClient(backend.hostname, backend.port)
                    self.runtime.backend_clients[backend_id] = client_backend

                cur_result = client_backend.ds_get_objects(
                    session_id,
                    objects_to_get,
                    already_obtained_objs,
                    recursive,
                    dest_replica_backend_id,
                    update_replica_locs,
                )
                logger.debug(
                    "[==GetObjectsInOtherBackend==] call return length: %d", len(cur_result)
                )
                logger.trace("[==GetObjectsInOtherBackend==] call return content: %s", cur_result)
                for res in cur_result:
                    result.append(res)

        return result

    def update_refs(self, ref_counting):
        """forward to SL"""
        self.runtime.backend_clients["@STORAGE"].update_refs(ref_counting)

    def get_retained_references(self):
        return self.runtime.get_retained_references()

    def detach_object_from_session(self, object_id, session_id):
        logger.debug(f"--> Detaching object {object_id} from session {session_id}")
        self.set_local_session(session_id)
        self.runtime.detach_object_from_session(object_id, None)
        logger.debug(f"<-- Detached object {object_id} from session {session_id}")

    # Tracing

    def activate_tracing(self, task_id):
        if not extrae_tracing_is_enabled():
            set_current_available_task_id(task_id)
            initialize_extrae(True)

    def deactivate_tracing(self):
        if extrae_tracing_is_enabled():
            finish_tracing(True)

    def get_traces(self):
        logger.debug("Merging...")
        return get_traces()
