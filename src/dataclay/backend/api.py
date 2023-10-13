""" Class description goes here. """

from __future__ import annotations

import concurrent.futures
import logging
import pickle
import time
import traceback
from collections.abc import Iterable
from typing import TYPE_CHECKING

from dataclay import utils
from dataclay.config import settings
from dataclay.exceptions import *
from dataclay.runtime import LockManager, set_runtime
from dataclay.runtime.backend import BackendRuntime
from dataclay.utils.serialization import dcdumps, recursive_dcloads
from dataclay.utils.telemetry import trace

if TYPE_CHECKING:
    from uuid import UUID

    from dataclay.dataclay_object import DataClayObject

tracer = trace.get_tracer(__name__)
logger = utils.LoggerEvent(logging.getLogger(__name__))


class BackendAPI:
    def __init__(self, name: str, port: int, kv_host: str, kv_port: int):
        # NOTE: the port is (atm) exclusively for unique identification of an EE
        # (given that the name is shared between all EE that share a SL, which happens in HPC deployments)
        self.name = name
        self.port = port

        # Initialize runtime
        self.backend_id = settings.backend.id
        self.runtime = BackendRuntime(kv_host, kv_port, self.backend_id)
        set_runtime(self.runtime)

        # UNDONE: Do not store EE information. If restarted, create new EE uuid.
        logger.info(f"Initialized backend {self.backend_id}")

    def is_ready(self, timeout: float | None = None, pause: float = 0.5):
        ref = time.time()
        now = ref
        if self.runtime.metadata_service.is_ready(timeout):
            # Check that dataclay_id is defined. If it is not defined, it could break things
            while timeout is None or (now - ref) < timeout:
                try:
                    dataclay_id = self.runtime.metadata_service.get_dataclay("this").id
                    settings.dataclay_id = dataclay_id
                    return True
                except DoesNotExistError:
                    time.sleep(pause)
                    now = time.time()

        return False

    # Object Methods
    def register_objects(self, serialized_objects: Iterable[bytes], make_replica: bool):
        for object_bytes in serialized_objects:
            object_dict, state = pickle.loads(object_bytes)

            instance = self.runtime.get_object_by_id(object_dict["_dc_meta"].id)

            if instance._dc_is_local:
                assert instance._dc_is_replica
                if make_replica:
                    logger.warning(f"There is already a replica for object {instance._dc_meta.id}")
                    continue

            with LockManager.write(instance._dc_meta.id):
                object_dict["_dc_is_loaded"] = True
                object_dict["_dc_is_local"] = True
                vars(instance).update(object_dict)
                if state:
                    instance.__setstate__(state)
                self.runtime.data_manager.add_hard_reference(instance)

                if make_replica:
                    instance._dc_is_replica = True
                    instance._dc_meta.replica_backend_ids.add(self.backend_id)

                else:
                    # If not make_replica then its a move
                    instance._dc_meta.master_backend_id = self.backend_id
                    instance._dc_meta.replica_backend_ids.discard(self.backend_id)
                    # we can only move masters
                    # instance._dc_is_replica = False # already set by vars(instance).update(object_dict)

                # ¿Should be always updated here, or from the calling backend?
                self.runtime.metadata_service.upsert_object(instance._dc_meta)

    @tracer.start_as_current_span("make_persistent")
    def make_persistent(self, serialized_objects: Iterable[bytes]):
        logger.info("Receiving objects to make persistent")
        unserialized_objects: dict[UUID, DataClayObject] = {}
        for object_bytes in serialized_objects:
            proxy_object = recursive_dcloads(object_bytes, unserialized_objects)
            proxy_object._dc_is_local = True
            proxy_object._dc_is_loaded = True
            proxy_object._dc_meta.master_backend_id = self.backend_id

        assert len(serialized_objects) == len(unserialized_objects)

        for proxy_object in unserialized_objects.values():
            logger.debug(
                f"({proxy_object._dc_meta.id}) Registering {proxy_object.__class__.__name__}"
            )
            self.runtime.inmemory_objects[proxy_object._dc_meta.id] = proxy_object
            self.runtime.data_manager.add_hard_reference(proxy_object)
            self.runtime.metadata_service.upsert_object(proxy_object._dc_meta)
            proxy_object._dc_is_registered = True

    @tracer.start_as_current_span("call_active_method")
    def call_active_method(
        self, session_id: UUID, object_id: UUID, method_name: str, args: tuple, kwargs: dict
    ) -> tuple[bytes, bool]:
        # logger.debug(f"({object_id}) Calling remote method {method_name}") # Critical Performance Hit

        # NOTE: Session (dataset) is needed for make_persistents inside dc_methods.
        self.runtime.set_session_by_id(session_id)
        instance = self.runtime.get_object_by_id(object_id)

        # NOTE: When the object is not local, a custom exception is sent
        # for the client to update the backend_id, and call_active_method again
        if not instance._dc_is_local:
            # NOTE: We sync the metadata because when consolidating an object
            # it might be that the proxy is pointing to the wrong backend_id which is
            # the same current backend, creating a infinite loop. This could be solve also
            # by passing the backend_id of the new object to the proxy, but this can create
            # problems with race conditions (e.g. a move before the consolidation). Therefore,
            # we check to the metadata which is more reliable.
            self.runtime.sync_object_metadata(instance)
            logger.warning(
                f"({object_id}) Wrong backend. Update to {instance._dc_meta.master_backend_id}"
            )
            return (
                pickle.dumps(
                    ObjectWithWrongBackendIdError(
                        instance._dc_meta.master_backend_id, instance._dc_meta.replica_backend_ids
                    )
                ),
                False,
            )

        args = pickle.loads(args)
        kwargs = pickle.loads(kwargs)

        try:
            value = getattr(instance, method_name)(*args, **kwargs)
            if value is not None:
                value = dcdumps(value)
            return value, False
        except Exception as e:
            return pickle.dumps(e), True

    # Store Methods

    @tracer.start_as_current_span("get_object_properties")
    def get_object_properties(self, object_id: UUID) -> bytes:
        """Returns the properties of the object with ID provided

        Args:
            object_id: ID of the object

        Returns:
            The pickled properties of the object.
        """
        instance = self.runtime.get_object_by_id(object_id)
        object_properties = self.runtime.get_object_properties(instance)
        return dcdumps(object_properties)

    @tracer.start_as_current_span("update_object_properties")
    def update_object_properties(self, object_id: UUID, serialized_properties: bytes):
        """Updates an object with ID provided with contents from another object"""
        instance = self.runtime.get_object_by_id(object_id)
        object_properties = pickle.loads(serialized_properties)
        self.runtime.update_object_properties(instance, object_properties)

    def new_object_version(self, object_id: UUID):
        """Creates a new version of the object with ID provided

        This entrypoint for new_version is solely for COMPSs (called from java).

        Args:
            object_id: ID of the object to create a new version from.

        Returns:
            The JSON-encoded metadata of the new DataClayObject version.
        """
        instance = self.runtime.get_object_by_id(object_id)

        # HACK: The dataset is needed to create a new version because
        # a new dataclay object is created and registered instantly in __new__
        # dataset_name = instance._dc_meta.dataset_name
        # self.runtime.session = Session(None, None, dataset_name)

        new_version = self.runtime.new_object_version(instance)
        return new_version.getID()

    def consolidate_object_version(self, object_id: UUID):
        """Consolidates the object with ID provided"""
        instance = self.runtime.get_object_by_id(object_id)
        self.runtime.consolidate_version(instance)

    @tracer.start_as_current_span("proxify_object")
    def proxify_object(self, object_id: UUID, new_object_id: UUID):
        instance = self.runtime.get_object_by_id(object_id)
        self.runtime.proxify_object(instance, new_object_id)

    @tracer.start_as_current_span("change_object_id")
    def change_object_id(self, object_id: UUID, new_object_id: UUID):
        instance = self.runtime.get_object_by_id(object_id)
        self.runtime.change_object_id(instance, new_object_id)

    @tracer.start_as_current_span("send_objects")
    def send_objects(
        self,
        object_ids: Iterable[UUID],
        backend_id: UUID,
        make_replica: bool,
        recursive: bool,
        remotes: bool,
    ):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            instances = tuple(executor.map(self.runtime.get_object_by_id, object_ids))
        self.runtime.send_objects(instances, backend_id, make_replica, recursive, remotes)

    # Shutdown

    @tracer.start_as_current_span("shutdown")
    def shutdown(self):
        self.runtime.stop()

    @tracer.start_as_current_span("flush_all")
    def flush_all(self):
        self.runtime.data_manager.flush_all()

    @tracer.start_as_current_span("move_all_objects")
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
            backends_objects[object_md.master_backend_id].append(object_md.id)

        backends_diff = {}
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

    def new_object_replica(
        self,
        object_id: UUID,
        backend_id: UUID = None,
        recursive: bool = False,
        remotes: bool = True,
    ):
        instance = self.runtime.get_object_by_id(object_id)
        self.runtime.new_object_replica(instance, backend_id, recursive, remotes)

    def synchronize(
        self, session_id, object_id, implementation_id, serialized_value, calling_backend_id=None
    ):
        raise Exception("To refactor")
        # set field
        logger.debug(
            f"----> Starting synchronization of {object_id} from calling backend {calling_backend_id}"
        )

        self.ds_exec_impl(object_id, implementation_id, serialized_value, session_id)
        instance = self.get_local_instance(object_id, True)
        src_exec_env_id = instance._dc_meta.master_backend_id()
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

        replica_locations = instance._dc_meta.replica_backend_ids
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
        raise Exception("To refactor")
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

        raise Exception("To refactor")
        self.set_local_session(session_id)

        try:
            logger.debug("----> Notified federation")

            # No need to provide params specs or param order since objects are not language types
            federated_objs = self.store_in_memory(objects_to_persist)

            # Register objects with alias (should we?)
            for object in federated_objs:
                if object._dc_alias:
                    self.runtime.metadata_service.upsert_object(object._dc_meta)

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
        raise Exception("To refactor")
        try:
            logger.debug("----> Starting unfederation of %s", object_id)
            object_ids = set()
            object_ids.add(object_id)
            serialized_objs = self.get_objects(
                session_id, object_ids, set(), recursive, external_execution_env_id, 2
            )

            unfederate_per_backend = {}

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
        raise Exception("To refactor")
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
