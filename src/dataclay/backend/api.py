""" Class description goes here. """

import logging
import pickle
import traceback
import uuid

from opentelemetry import trace

from dataclay import utils
from dataclay.backend.client import BackendClient
from dataclay.conf import settings
from dataclay.exceptions.exceptions import DataClayException
from dataclay.runtime import UUIDLock, set_runtime
from dataclay.runtime.backend_runtime import BackendRuntime

tracer = trace.get_tracer(__name__)
logger = utils.LoggerEvent(logging.getLogger(__name__))


class BackendAPI:
    def __init__(self, theee_name, theee_port, etcd_host, etcd_port):

        # NOTE: the port is (atm) exclusively for unique identification of an EE
        # (given that the name is shared between all EE that share a SL, which happens in HPC deployments)
        self.ee_name = theee_name
        self.ee_port = theee_port

        # Initialize runtime
        self.runtime = BackendRuntime(self, etcd_host, etcd_port)
        set_runtime(self.runtime)

        # UNDONE: Do not store EE information. If restarted, create new EE uuid.
        self.execution_environment_id = uuid.uuid4()
        logger.info(f"Initialized EE with ID: {self.execution_environment_id}")

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

    def get_object_metadata(self, object_id):
        """Get the MetaDataInfo for a certain object.

        If we have it available in the cache, return it. Otherwise, call the
        MetadataService for it.

        Args:
            object_id: The ID of the persistent object

        Returns:
            The MetaData for the given object.
        """

        logger.info(f"Getting MetaData for object {object_id}")

        try:
            return self.runtime.inmemory_objects[object_id].metadata
        except KeyError:
            return self.runtime.metadata_service.get_object_md_by_id(object_id)

    def get_local_instance(self, object_id, retry=True):
        return self.runtime.get_or_new_instance_from_db(object_id, retry)

    def set_local_session(self, session_id: uuid.UUID):
        """Check and set the session to thread_local_data.

        Args:
            session_id: The session's UUID.
        """
        session = self.runtime.metadata_service.get_session(session_id)
        self.runtime.session = session

    def update_hints_to_current_ee(self, objects_data_to_store):
        """Update hints in serialized objects provided to use current backend id

        Args:
            objects_data_to_store: serialized objects to update
        """
        ## Update hints since this function is called from other backends
        hints_mapping = dict()
        for cur_obj_data in objects_data_to_store:
            object_id = cur_obj_data.object_id
            hints_mapping[object_id] = self.execution_environment_id

        for cur_obj_data in objects_data_to_store:
            object_id = cur_obj_data.object_id
            metadata = cur_obj_data.metadata
            obj_bytes = cur_obj_data.obj_bytes
            metadata.modify_hints(hints_mapping)
            # make persistent - session references
            try:
                self.runtime.add_session_reference(object_id)
            except Exception as e:
                # TODO: See exception in set_local_session
                logger.debug(
                    "Trying to add_session_reference during store of a federated object"
                    "in a federated dataclay ==> Provided dataclayID instead of sessionID"
                )
                pass

    def store_objects(self, session_id, objects_data_to_store, moving, ids_with_alias):
        """Store objects in DB

        Args:
            session_id: ID of session storing objects
            objects_data_to_store: Objects Data to store
            moving: Indicates if store is done during a move
            ids_with_alias: IDs with alias
        """
        self.set_local_session(session_id)

        self.update_hints_to_current_ee(objects_data_to_store)
        self.store_in_memory(objects_data_to_store)

    def register_and_store_pending(self, instance, obj_bytes, sync):

        object_id = instance._dc_id

        # NOTE: we are doing *two* remote calls, and wishlist => they work as a transaction
        self.runtime.backend_clients["@STORAGE"].store_to_db(
            self.execution_environment_id, object_id, obj_bytes
        )

        # TODO: When the object metadata is updated synchronously, this should me removed
        self.runtime.metadata_service.update_object(instance.metadata)

        instance._dc_is_pending_to_register = False

    def store_in_memory(self, objects_to_store):
        """This function will deserialize objects into dataClay memory heap using the same design as for
        volatile parameters. Eventually, dataClay GC will collect them, and then they will be
        registered in LogicModule if needed (if objects were created with alias, they must
        have metadata already).

        Args:
            session_id: ID of session of make persistent call
            objects_to_store: objects to store.
        """

        # No need to provide params specs or param order since objects are not language types
        vol_objs = dict()
        i = 0
        for object_to_store in objects_to_store:
            vol_objs[i] = object_to_store
            i = i + 1
        return DeserializationLibUtilsSingleton.deserialize_params(
            SerializedParametersOrReturn(num_params=i, vol_objs=vol_objs),
            None,
            None,
            None,
            self.runtime,
        )

    def new_make_persistent(self, session_id: uuid.UUID, serialized_dict: bytes):
        self.set_local_session(session_id)

        # Deserialize __dict__
        dict = pickle.loads(serialized_dict)

        # NOTE: In case of circular dependencies, it is possible that
        # the volatile object is stored in the heap as a persistent object.
        # In this case we must update the persistent instance already stored.
        # TODO: Remove the try when the new make_persistent is implemented.
        # This new_make_persistent should send all the objects (even with circular dependencies)
        # in one call to the EE
        try:
            instance = self.runtime.inmemory_objects[dict["_dc_id"]]
            instance.__dict__.update(dict)
            instance._dc_is_persistent = True  # All objects in the EE are persistent
            instance._dc_is_loaded = True
            instance._dc_is_pending_to_register = True
            instance._dc_master_ee_id = self.runtime.get_hint()  # It should be already defined
        except KeyError:
            instance = dict["_dc_class"].new_volatile(**dict)

        print("\n*** unpickled_obj:", type(instance))
        print("*** unpickled_obj:", instance._dc_id)
        print("*** unpickled_obj:", instance.__dict__, end="\n\n")

        self.runtime.metadata_service.register_object(instance.metadata)

    ###############
    # active method
    ###############

    def call_active_method(self, session_id, object_id, method_name, args, kwargs):
        self.set_local_session(session_id)

        instance = self.get_local_instance(object_id, True)
        args = pickle.loads(args)
        kwargs = pickle.loads(kwargs)

        returned_value = self.runtime.call_active_method(instance, method_name, args, kwargs)

        if returned_value is not None:
            return pickle.dumps(returned_value)

    #######
    # Clone
    #######

    def get_copy_of_object(self, session_id, object_id, recursive):
        """Returns a non-persistent copy of the object with ID provided

        Args:
            session_id: ID of session
            object_id: ID of the object
        Returns:
            the generated non-persistent objects
        """
        logger.debug("[==Get==] Get copy of %s ", object_id)

        # Get the data service of one of the backends that contains the original object.
        object_ids = set()
        object_ids.add(object_id)

        serialized_objs = self.get_objects(session_id, object_ids, set(), recursive, None, 0)

        # Prepare OIDs
        logger.debug("[==Get==] Serialized objects obtained to create a copy of %s", object_id)
        original_to_version = dict()

        # Store version in this backend (if already stored, just skip it)
        for obj_with_param_or_return in serialized_objs:
            orig_obj_id = obj_with_param_or_return.object_id
            version_obj_id = uuid.uuid4()
            original_to_version[orig_obj_id] = version_obj_id

        for obj_with_param_or_return in serialized_objs:
            orig_obj_id = obj_with_param_or_return.object_id
            version_obj_id = original_to_version[orig_obj_id]
            metadata = obj_with_param_or_return.metadata
            self._modify_metadata_oids(metadata, original_to_version)
            obj_with_param_or_return.object_id = version_obj_id

        i = 0
        imm_objs = dict()
        lang_objs = dict()
        vol_params = dict()
        pers_params = dict()
        for obj in serialized_objs:
            vol_params[i] = obj
            i = i + 1

        serialized_result = SerializedParametersOrReturn(
            num_params=i,
            imm_objs=imm_objs,
            lang_objs=lang_objs,
            vol_objs=vol_params,
            pers_objs=pers_params,
        )

        return serialized_result

    ######
    # Move
    ######

    def move_objects(self, session_id, object_id, dest_backend_id, recursive):
        """This operation removes the objects with IDs provided

         This function is recursive, it is going to other DSs if needed.

        Args:
            session_id: ID of session.
            object_id: ID of the object to move.
            dest_backend_id: ID of the backend where to move.
            recursive: Indicates if all sub-objects (in this location or others) must be moved as well.

        Returns:
            Set of moved objects.
        """
        update_metadata_of = set()

        try:
            logger.debug(
                "[==MoveObjects==] Moving object %s to storage location: %s",
                object_id,
                dest_backend_id,
            )
            object_ids = set()
            object_ids.add(object_id)

            # TODO: Object being used by session (any oid in the method header) G.C.

            serialized_objs = self.get_objects(session_id, object_ids, set(), True, None, 0)
            objects_to_remove = set()
            objects_to_move = list()

            for obj_found in serialized_objs:
                logger.debug("[==MoveObjects==] Looking for metadata of %s", obj_found[0])
                object_md = self.get_object_metadata(obj_found[0])
                obj_location = object_md.master_ee_id

                if obj_location == dest_backend_id:
                    logger.debug(
                        "[==MoveObjects==] Ignoring move of object %s since it is already where it should be."
                        " ObjLoc = %s and DestLoc = %s",
                        obj_found[0],
                        obj_location,
                        dest_backend_id,
                    )

                    # object already in dest
                    pass
                else:
                    if settings.storage_id == dest_backend_id:
                        # THE DESTINATION IS HERE
                        if obj_location != settings.storage_id:
                            logger.debug(
                                "[==MoveObjects==] Moving object  %s since dest.location is different to src.location and object is not in dest.location."
                                " ObjLoc = %s and DestLoc = %s",
                                obj_found[0],
                                obj_location,
                                dest_backend_id,
                            )
                            objects_to_move.append(obj_found)
                            objects_to_remove.add(obj_found[0])
                            update_metadata_of.add(obj_found[0])
                        else:
                            logger.debug(
                                "[==MoveObjects==] Ignoring move of object %s since it is already where it should be"
                                " ObjLoc = %s and DestLoc = %s",
                                obj_found[0],
                                obj_location,
                                dest_backend_id,
                            )
                    else:
                        logger.debug(
                            "[==MoveObjects==] Moving object %s since dest.location is different to src.location and object is not in dest.location "
                            " ObjLoc = %s and DestLoc = %s",
                            obj_found[0],
                            obj_location,
                            dest_backend_id,
                        )
                        # THE DESTINATION IS ANOTHER NODE: move.
                        objects_to_move.append(obj_found)
                        objects_to_remove.add(obj_found[0])
                        update_metadata_of.add(obj_found[0])

            logger.debug("[==MoveObjects==] Finally moving OBJECTS: %s", objects_to_remove)

            try:
                sl_client = self.runtime.backend_clients[dest_backend_id]
            except KeyError:
                st_loc = self.runtime.ee_infos[dest_backend_id]
                logger.debug(
                    "Not found in cache ExecutionEnvironment {%s}! Starting it at %s:%d",
                    dest_backend_id,
                    st_loc.hostname,
                    st_loc.port,
                )
                sl_client = BackendClient(st_loc.hostname, st_loc.port)
                self.runtime.backend_clients[dest_backend_id] = sl_client

            sl_client.ds_store_objects(session_id, objects_to_move, True, None)

            # TODO: lock any execution in remove before storing objects in remote dataservice so anyone can modify it.
            # Remove after store in order to avoid wrong executions during the movement :)
            # Remove all objects in all source locations different to dest. location
            # TODO: Check that remove is not necessary (G.C. Should do it?)
            # self.runtime.backend_clients["@STORAGE"].ds_remove_objects(session_id, object_ids, recursive, True, dest_backend_id)

            for oid in objects_to_remove:
                self.runtime.remove_metadata_from_cache(oid)
            logger.debug("[==MoveObjects==] Move finalized ")

        except Exception as e:
            logger.error("[==MoveObjects==] Exception %s", e.args)

        return update_metadata_of

    ##########
    # Replicas
    ##########

    def get_dest_ee_api(self, dest_backend_id):
        """Get API to connect to destination Execution environment with id provided

        Args:
            dest_backend_id: ID of destination backend
        """
        backend = self.runtime.get_execution_environment_info(dest_backend_id)
        try:
            client_backend = self.runtime.backend_clients[dest_backend_id]
        except KeyError:
            logger.debug(
                "Not found Client to ExecutionEnvironment {%s}!" " Starting it at %s:%d",
                dest_backend_id,
                backend.hostname,
                backend.port,
            )
            client_backend = BackendClient(backend.hostname, backend.port)
            self.runtime.backend_clients[dest_backend_id] = client_backend
        return client_backend

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
        client_backend = self.get_dest_ee_api(dest_backend_id)
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
        src_exec_env_id = instance.get_origin_location()
        if src_exec_env_id is not None:
            logger.debug(f"Found origin location {src_exec_env_id}")
            if calling_backend_id is None or src_exec_env_id != calling_backend_id:
                # do not synchronize to calling source (avoid infinite loops)
                dest_backend = self.get_dest_ee_api(src_exec_env_id)
                logger.debug(
                    f"----> Propagating synchronization of {object_id} to origin location {src_exec_env_id}"
                )

                dest_backend.synchronize(
                    session_id,
                    object_id,
                    implementation_id,
                    serialized_value,
                    calling_backend_id=self.execution_environment_id,
                )

        replica_locations = instance._dc_replica_ee_ids
        if replica_locations is not None:
            logger.debug(f"Found replica locations {replica_locations}")
            for replica_location in replica_locations:
                if calling_backend_id is None or replica_location != calling_backend_id:
                    # do not synchronize to calling source (avoid infinite loops)
                    dest_backend = self.get_dest_ee_api(replica_location)
                    logger.debug(
                        f"----> Propagating synchronization of {object_id} to replica location {replica_location}"
                    )
                    dest_backend.synchronize(
                        session_id,
                        object_id,
                        implementation_id,
                        serialized_value,
                        calling_backend_id=self.execution_environment_id,
                    )
        logger.debug(f"----> Finished synchronization of {object_id}")

    ############
    # Federation
    ############

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
        client_backend = self.get_dest_ee_api(external_execution_env_id)
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
                client_backend = self.get_dest_ee_api(external_ee_id)
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

    ###############
    # Update Object
    ###############

    def update_object(self, session_id, into_object_id, from_object):
        raise ("update_object need to be refactored")
        """Updates an object with ID provided with contents from another object

        Args:
            session_id: ID of session
            into_object_id: ID of the object to be updated
            from_object: object with contents to be used
        """
        self.set_local_session(session_id)
        logger.debug("[==PutObject==] Updating object %s", into_object_id)
        object_into = self.runtime.get_or_new_instance_from_db(into_object_id, False)
        object_from = DeserializationLibUtilsSingleton.deserialize_params_or_return(
            from_object, None, None, None, self.runtime
        )[0]
        object_into.set_all(object_from)
        logger.debug(
            "[==PutObject==] Updated object %s from object %s",
            into_object_id,
            object_from._dc_id,
        )

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
                    if current_hint is not None and current_hint != self.execution_environment_id:
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
                if current_obj._dc_replica_ee_ids is not None:
                    if dest_replica_backend_id in current_obj._dc_replica_ee_ids:
                        # already replicated
                        logger.debug(f"WARNING: Found already replicated object {oid}. Skipping")
                        return None

            # Add object to result and obtained_objs for return and recursive
            obj_with_data = SerializationLibUtilsSingleton.serialize_dcobj_with_data(
                current_obj, pending_objs, False, current_obj._dc_master_ee_id, self.runtime, False
            )

            if dest_replica_backend_id is not None and update_replica_locs == 1:
                current_obj.add_replica_location(dest_replica_backend_id)
                current_obj._dc_is_dirty = True
                obj_with_data.metadata.origin_location = self.execution_environment_id
            elif update_replica_locs == 2:
                if dest_replica_backend_id is not None:
                    current_obj.remove_replica_location(dest_replica_backend_id)
                else:
                    current_obj.clear_replica_locations()
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
        result = list()

        # Prepare to unify calls (only one call for DS)
        objects_per_backend = dict()

        for curr_oid_and_hint in objects_in_other_backend:
            object_id = curr_oid_and_hint[0]
            hint = curr_oid_and_hint[1]

            if hint is None:
                logger.debug(f"[==GetObjectsInOtherBackend==] Looking for metadata of {object_id}")
                object_md = self.get_object_metadata(object_id)
                hint = object_md.master_ee_id
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

    def new_version(self, session_id, object_id, dest_backend_id):
        """Creates a new version of the object with ID provided in the backend specified.

        Args:
            session_id: ID of session
            object_id: ID of the object
            dest_backend_id: Destination in which version must be created
        """
        logger.debug("----> Starting new version of %s", object_id)

        # Get the data service of one of the backends that contains the original object.
        object_ids = set()
        object_ids.add(object_id)
        serialized_objs = self.get_objects(session_id, object_ids, set(), True, None, 1)

        # Prepare OIDs
        original_to_version = dict()

        # Store version in this backend (if already stored, just skip it)
        for obj_with_data in serialized_objs:
            orig_obj_id = obj_with_data.object_id
            version_obj_id = uuid.uuid4()
            original_to_version[orig_obj_id] = version_obj_id

        for obj_with_param_or_return in serialized_objs:
            orig_obj_id = obj_with_param_or_return.object_id
            version_obj_id = original_to_version[orig_obj_id]
            metadata = obj_with_param_or_return.metadata
            self._modify_metadata_oids(metadata, original_to_version)
            if metadata.orig_object_id is None:
                # IMPORTANT: only set if not already set since consolidate
                # is always applied to original one
                metadata.orig_object_id = orig_obj_id
                metadata.root_location = self.execution_environment_id
            obj_with_param_or_return.object_id = version_obj_id

        if dest_backend_id == self.execution_environment_id:
            self.store_objects(session_id, serialized_objs, False, None)
        else:
            client_backend = self.get_dest_ee_api(dest_backend_id)
            client_backend.ds_store_objects(session_id, serialized_objs, False, None)
        version_obj_id = original_to_version[object_id]
        logger.debug(f"<---- Finished new version of {object_id} as {version_obj_id}")
        return version_obj_id

    def consolidate_version(self, session_id, final_version_id):
        """Consolidates object with id provided

        Args:
            session_id:ID of session
            final_version_id: ID of final version object
        """
        self.set_local_session()
        logger.debug("----> Starting consolidate version of %s", final_version_id)

        # Consolidate in this backend - the complete version is here
        object_ids = set()
        object_ids.add(final_version_id)
        serialized_objs = self.get_objects(session_id, object_ids, set(), True, None, 0)

        root_location = None

        version_to_original = dict()
        for serialized_obj in serialized_objs:
            version_id = serialized_obj.object_id
            original_md = serialized_obj.metadata
            if original_md.orig_object_id is not None:
                version_to_original[version_id] = original_md.orig_object_id
            if version_id == final_version_id:
                root_location = original_md.root_location

        serialized_objs_updated = list()
        for serialized_obj in serialized_objs:
            original_md = serialized_obj.metadata
            self._modify_metadata_oids(original_md, version_to_original)
            if original_md.orig_object_id is not None:
                serialized_obj.object_id = original_md.orig_object_id
            serialized_objs_updated.append(serialized_obj)

        try:
            if root_location == self.execution_environment_id:
                self.upsert_objects(session_id, serialized_objs_updated)
            else:
                client_backend = self.get_dest_ee_api(root_location)
                client_backend.ds_upsert_objects(session_id, serialized_objs_updated)
        except Exception as e:
            traceback.print_exc()
            logger.error("Exception during Consolidate Version")
            raise e
        logger.debug("<---- Finished consolidate of %s", final_version_id)

    def _modify_metadata_oids(self, metadata, original_to_version):
        """Modify the version's metadata in serialized_objs with original OID"""

        logger.debug("[==ModifyMetadataOids==] Modify metadata object %r", metadata)
        logger.debug("[==ModifyMetadataOids==] Version OIDs Map: %s", original_to_version)

        for tag, oid in metadata.tags_to_oids.items():
            try:
                metadata.tags_to_oids[tag] = original_to_version[oid]
            except KeyError:
                logger.debug(
                    "[==ModifyMetadataOids==] oid %s is not mapped => object added in the version",
                    oid,
                )
                # obj[2][0][tag] = oid
                pass

        logger.debug("[==ModifyMetadataOids==] Object with modified metadata is %r", metadata)

    def upsert_objects(self, session_id, object_ids_and_bytes):
        """Updates objects or insert if they do not exist with the values in objectBytes.

        This function is recursive, it is going to other DSs if needed.

        Args:
            session_id: ID of session needed.
            object_ids_and_bytes: Map of objects to update.
        """
        self.set_local_session()

        try:
            objects_in_other_backends = list()
            updated_objects_here = list()

            # To check for replicas
            for cur_entry in object_ids_and_bytes:
                # ToDo: G.C. stuffs
                object_id = cur_entry.object_id
                logger.debug("[==Upsert==] Updated or inserted object %s", object_id)
                try:
                    # Update bytes at memory object
                    logger.debug(
                        "[==Upsert==] Getting/Creating instance from upsert with id %s", object_id
                    )
                    instance = self.runtime.get_or_new_instance_from_db(object_id, False)
                    DeserializationLibUtilsSingleton.deserialize_object_with_data(
                        cur_entry,
                        instance,
                        None,
                        self.runtime,
                        self.runtime.session.id,
                        True,
                    )

                    instance._dc_is_dirty = True
                    updated_objects_here.append(cur_entry)
                except Exception:
                    # Get in other backend
                    objects_in_other_backends.append(cur_entry)

            self.update_hints_to_current_ee(updated_objects_here)
            self.upsert_objects_in_other_backend(session_id, objects_in_other_backends)

        except Exception as e:
            traceback.print_exc()
            logger.error("Exception during Upsert Objects")
            raise e

    def upsert_objects_in_other_backend(self, session_id, objects_in_other_backends):
        """Update object in another backend.

        Args:
            session_id: ID of session
            objects_in_other_backends: List of metadata of objects to update and its bytes. It is useful to avoid multiple trips.

        Returns:
            ID of objects and for each object, its bytes.
        """
        # Prepare to unify calls (only one call for DS)
        objects_per_backend = dict()
        for curr_obj_with_ids in objects_in_other_backends:

            object_id = curr_obj_with_ids[0]
            object_md = self.get_object_metadata(object_id)
            location = object_md.master_ee_id
            # Update object at first location (NOT UPDATING REPLICAS!!!)
            try:
                objects_in_backend = objects_per_backend[location]
            except KeyError:
                objects_in_backend = list()
                objects_per_backend[location] = objects_in_backend

            objects_in_backend.append(curr_obj_with_ids)
        # Now Call
        for backend_id, objects_to_update in objects_per_backend.items():

            backend = self.runtime.get_execution_environment_info(backend_id)

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

            client_backend.ds_upsert_objects(session_id, objects_to_update)

    def update_refs(self, ref_counting):
        """forward to SL"""
        self.runtime.backend_clients["@STORAGE"].update_refs(ref_counting)

    def get_retained_references(self):
        return self.runtime.get_retained_references()

    def close_session_in_ee(self, session_id):
        self.runtime.close_session_in_ee(session_id)

    def detach_object_from_session(self, object_id, session_id):
        logger.debug(f"--> Detaching object {object_id} from session {session_id}")
        self.set_local_session(session_id)
        self.runtime.detach_object_from_session(object_id, None)
        logger.debug(f"<-- Detached object {object_id} from session {session_id}")

    #######
    # Alias
    #######

    def delete_alias(self, session_id, object_id):
        self.set_local_session(session_id)
        instance = self.get_local_instance(object_id, True)
        self.runtime.delete_alias(instance)

    def get_num_objects(self):
        return self.runtime.count_loaded_objs()

    ##########
    # Shutdown
    ##########

    def stop(self):
        self.runtime.stop_gc()
        self.runtime.flush_all()
        # TODO: delete the EE entry in ETCD using MetadataService, or use Lease

    #########
    # Tracing
    #########

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

    ################## EXTRAE IGNORED FUNCTIONS ###########################
    deactivate_tracing.do_not_trace = True
    activate_tracing.do_not_trace = True
