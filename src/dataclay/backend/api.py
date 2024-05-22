""" Class description goes here. """

from __future__ import annotations

import asyncio
import logging
import pickle
import time
import traceback
from collections.abc import Iterable
from typing import TYPE_CHECKING, Optional

from dataclay import utils
from dataclay.config import set_runtime, settings
from dataclay.event_loop import dc_to_thread
from dataclay.exceptions import DoesNotExistError, ObjectWithWrongBackendIdError
from dataclay.lock_manager import lock_manager
from dataclay.runtime import BackendRuntime
from dataclay.utils.serialization import dcdumps, dcloads, recursive_dcloads
from dataclay.utils.telemetry import trace

if TYPE_CHECKING:
    from uuid import UUID

    from dataclay.dataclay_object import DataClayObject

tracer = trace.get_tracer(__name__)
logger = utils.LoggerEvent(logging.getLogger(__name__))


class BackendAPI:
    def __init__(self, name: str, port: int, backend_id: UUID, kv_host: str, kv_port: int):
        # NOTE: the port is (atm) exclusively for unique identification of an EE
        # (given that the name is shared between all EE that share a SL, which happens in HPC deployments)
        self.name = name
        self.port = port

        # Initialize runtime
        self.backend_id = backend_id
        self.runtime = BackendRuntime(kv_host, kv_port, self.backend_id)
        set_runtime(self.runtime)

    async def is_ready(self, timeout: Optional[float] = None, pause: float = 0.5):
        ref = time.time()
        now = ref
        if await self.runtime.metadata_service.is_ready(timeout):
            # Check that dataclay_id is defined. If it is not defined, it could break things
            while timeout is None or (now - ref) < timeout:
                try:
                    dataclay_obj = await self.runtime.metadata_service.get_dataclay("this")
                    settings.dataclay_id = dataclay_obj.id
                    return True
                except DoesNotExistError:
                    time.sleep(pause)
                    now = time.time()

        return False

    # Object Methods
    async def register_objects(self, serialized_objects: Iterable[bytes], make_replica: bool):
        logger.debug("Receiving (%d) objects to register", len(serialized_objects))
        for object_bytes in serialized_objects:
            state, getstate = await dcloads(object_bytes)
            instance = await self.runtime.get_object_by_id(state["_dc_meta"].id)

            if instance._dc_is_local:
                assert instance._dc_is_replica
                if make_replica:
                    logger.warning("Replica already exists with id=%s", instance._dc_meta.id)
                    continue

            async with lock_manager.get_lock(instance._dc_meta.id).writer_lock:
                # Update object state and flags
                state["_dc_is_loaded"] = True
                state["_dc_is_local"] = True
                vars(instance).update(state)
                if getstate:
                    instance.__setstate__(getstate)
                self.runtime.data_manager.add_hard_reference(instance)

                if make_replica:
                    instance._dc_is_replica = True
                    instance._dc_meta.replica_backend_ids.add(self.backend_id)

                else:
                    # If not make_replica then its a move
                    instance._dc_meta.master_backend_id = self.backend_id
                    instance._dc_meta.replica_backend_ids.discard(self.backend_id)
                    # we can only move masters
                    # instance._dc_is_replica = False # already set by vars(instance).update(state)

                # ¿Should be always updated here, or from the calling backend?
                await self.runtime.metadata_service.upsert_object(instance._dc_meta)

    @tracer.start_as_current_span("make_persistent")
    async def make_persistent(self, serialized_objects: Iterable[bytes]):
        logger.debug("Receiving (%d) objects to make persistent", len(serialized_objects))
        unserialized_objects: dict[UUID, DataClayObject] = {}
        for object_bytes in serialized_objects:
            proxy_object = await recursive_dcloads(object_bytes, unserialized_objects)
            proxy_object._dc_is_local = True
            proxy_object._dc_is_loaded = True
            proxy_object._dc_meta.master_backend_id = self.backend_id

        assert len(serialized_objects) == len(unserialized_objects)

        for proxy_object in unserialized_objects.values():
            logger.debug(
                "(%s) Registering %s",
                proxy_object._dc_meta.id,
                proxy_object.__class__.__name__,
            )
            self.runtime.inmemory_objects[proxy_object._dc_meta.id] = proxy_object
            self.runtime.data_manager.add_hard_reference(proxy_object)
            await self.runtime.metadata_service.upsert_object(proxy_object._dc_meta)
            proxy_object._dc_is_registered = True

    @tracer.start_as_current_span("call_active_method")
    async def call_active_method(
        self, object_id: UUID, method_name: str, args: tuple, kwargs: dict
    ) -> tuple[bytes, bool]:
        """Entry point for calling an active method of a DataClayObject"""

        logger.debug("(%s) Receiving call to activemethod '%s'", object_id, method_name)

        instance = await self.runtime.get_object_by_id(object_id)

        # If the object isn't local (not owned by this backend), a custom exception is sent to the
        # client to update the object's backend_id, and call_active_method again to the correct backend
        if not instance._dc_is_local:
            # NOTE: We sync the metadata because when consolidating an object
            # it might be that the proxy is pointing to the wrong backend_id which is
            # the same current backend, creating a infinite loop. This could be solve also
            # by passing the backend_id of the new object to the proxy, but this can create
            # problems with race conditions (e.g. a move before the consolidation). Therefore,
            # we check to the metadata which is more reliable.
            await self.runtime.sync_object_metadata(instance)
            logger.warning(
                "(%s) Wrong backend. Update to %s",
                object_id,
                instance._dc_meta.master_backend_id,
            )
            return (
                pickle.dumps(
                    ObjectWithWrongBackendIdError(
                        instance._dc_meta.master_backend_id, instance._dc_meta.replica_backend_ids
                    )
                ),
                False,
            )

        # Deserialize arguments
        args, kwargs = await asyncio.gather(dcloads(args), dcloads(kwargs))

        try:
            # Call activemethod in another thread
            logger.debug("(%s) *** Starting activemethod '%s' in executor", object_id, method_name)
            result = await dc_to_thread(getattr(instance, method_name), *args, **kwargs)
            logger.debug("(%s) *** Finished activemethod '%s' in executor", object_id, method_name)

            # Serialize the result if not None
            if result is None:
                return result, False
            else:
                result_bytes = await dcdumps(result)
                return result_bytes, False
        except Exception as e:
            # If an exception was raised, serialize it and return it to be raised by the client
            return pickle.dumps(e), True

    # Store Methods

    # TODO: Rename to get_object_property
    @tracer.start_as_current_span("get_object_attribute")
    async def get_object_attribute(self, object_id: UUID, attribute: str) -> tuple[bytes, bool]:
        """Returns value of the object attibute with ID provided
        Args:
            object_id: ID of the object
            attribute: Name of the attibute
        Returns:
            The pickled value of the object attibute.
            If it's an exception or not
        """
        logger.debug("(%s) Receiving get attribute '%s'", object_id, attribute)
        instance = await self.runtime.get_object_by_id(object_id)
        if not instance._dc_is_local:
            await self.runtime.sync_object_metadata(instance)
            logger.warning(
                "(%s) Wrong backend. Update to %s",
                object_id,
                instance._dc_meta.master_backend_id,
            )
            return (
                pickle.dumps(
                    ObjectWithWrongBackendIdError(
                        instance._dc_meta.master_backend_id, instance._dc_meta.replica_backend_ids
                    )
                ),
                False,
            )
        try:
            value = await dc_to_thread(getattr, instance, attribute)
            return await dcdumps(value), False
        except Exception as e:
            return pickle.dumps(e), True

    # TODO: Rename to set_object_property
    @tracer.start_as_current_span("set_object_attribute")
    async def set_object_attribute(
        self, object_id: UUID, attribute: str, serialized_attribute: bytes
    ) -> tuple[bytes, bool]:
        """Updates an object attibute with ID provided"""
        logger.debug("(%s) Receiving set attribute '%s'", object_id, attribute)
        instance = await self.runtime.get_object_by_id(object_id)
        if not instance._dc_is_local:
            await self.runtime.sync_object_metadata(instance)
            logger.warning(
                "(%s) Wrong backend. Update to %s",
                object_id,
                instance._dc_meta.master_backend_id,
            )

            return (
                pickle.dumps(
                    ObjectWithWrongBackendIdError(
                        instance._dc_meta.master_backend_id, instance._dc_meta.replica_backend_ids
                    )
                ),
                False,
            )
        try:
            object_attribute = await dcloads(serialized_attribute)
            await dc_to_thread(setattr, instance, attribute, object_attribute)
            return None, False
        except Exception as e:
            return pickle.dumps(e), True

    @tracer.start_as_current_span("del_object_attribute")
    async def del_object_attribute(self, object_id: UUID, attribute: str) -> tuple[bytes, bool]:
        """Deletes an object attibute with ID provided"""
        instance = await self.runtime.get_object_by_id(object_id)
        if not instance._dc_is_local:
            await self.runtime.sync_object_metadata(instance)
            logger.warning(
                "(%s) Wrong backend. Update to %s",
                object_id,
                instance._dc_meta.master_backend_id,
            )
            return (
                pickle.dumps(
                    ObjectWithWrongBackendIdError(
                        instance._dc_meta.master_backend_id, instance._dc_meta.replica_backend_ids
                    )
                ),
                False,
            )
        try:
            await dc_to_thread(delattr, instance, attribute)
            return None, False
        except Exception as e:
            return pickle.dumps(e), True

    @tracer.start_as_current_span("get_object_properties")
    async def get_object_properties(self, object_id: UUID) -> bytes:
        """Returns the properties of the object with ID provided

        Args:
            object_id: ID of the object

        Returns:
            The pickled properties of the object.
        """
        instance = await self.runtime.get_object_by_id(object_id)
        object_properties = await self.runtime.get_object_properties(instance)
        return await dcdumps(object_properties)

    @tracer.start_as_current_span("update_object_properties")
    async def update_object_properties(self, object_id: UUID, serialized_properties: bytes):
        """Updates an object with ID provided with contents from another object"""
        instance, object_properties = await asyncio.gather(
            self.runtime.get_object_by_id(object_id), dcloads(serialized_properties)
        )
        await self.runtime.update_object_properties(instance, object_properties)

    async def new_object_version(self, object_id: UUID):
        """Creates a new version of the object with ID provided

        This entrypoint for new_version is solely for COMPSs (called from java).

        Args:
            object_id: ID of the object to create a new version from.

        Returns:
            The JSON-encoded metadata of the new DataClayObject version.
        """
        instance = await self.runtime.get_object_by_id(object_id)
        new_version = await self.runtime.new_object_version(instance)
        return new_version.getID()

    async def consolidate_object_version(self, object_id: UUID):
        """Consolidates the object with ID provided"""
        instance = await self.runtime.get_object_by_id(object_id)
        await self.runtime.consolidate_version(instance)

    @tracer.start_as_current_span("proxify_object")
    async def proxify_object(self, object_id: UUID, new_object_id: UUID):
        """Proxify object with ID provided to new object ID"""
        logger.debug("Proxifying object %s to %s", object_id, new_object_id)
        instance = await self.runtime.get_object_by_id(object_id)
        await self.runtime.proxify_object(instance, new_object_id)

    @tracer.start_as_current_span("change_object_id")
    async def change_object_id(self, object_id: UUID, new_object_id: UUID):
        instance = await self.runtime.get_object_by_id(object_id)
        await self.runtime.change_object_id(instance, new_object_id)

    @tracer.start_as_current_span("send_objects")
    async def send_objects(
        self,
        object_ids: Iterable[UUID],
        backend_id: UUID,
        make_replica: bool,
        recursive: bool,
        remotes: bool,
    ):
        logger.debug("Receiving objects to %s", "replicate" if make_replica else "move")
        # Use asyncio.gather to call get_object_by_id concurrently for all object_ids
        instances = await asyncio.gather(
            *[self.runtime.get_object_by_id(object_id) for object_id in object_ids]
        )
        await self.runtime.send_objects(instances, backend_id, make_replica, recursive, remotes)

    # Shutdown

    @tracer.start_as_current_span("stop")
    async def stop(self):
        await self.runtime.stop()

    @tracer.start_as_current_span("flush_all")
    async def flush_all(self):
        await self.runtime.data_manager.flush_all()

    @tracer.start_as_current_span("move_all_objects")
    async def move_all_objects(self):
        dc_objects = await self.runtime.metadata_service.get_all_objects()
        await self.runtime.backend_clients.update()
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

    async def new_object_replica(
        self,
        object_id: UUID,
        backend_id: UUID = None,
        recursive: bool = False,
        remotes: bool = True,
    ):
        instance = await self.runtime.get_object_by_id(object_id)
        await self.runtime.new_object_replica(instance, backend_id, recursive, remotes)

    def synchronize(
        self, session_id, object_id, implementation_id, serialized_value, calling_backend_id=None
    ):
        raise Exception("To refactor")
        # set field
        logger.debug(
            "----> Starting synchronization of %s from calling backend %s",
            object_id,
            calling_backend_id,
        )

        self.ds_exec_impl(object_id, implementation_id, serialized_value, session_id)
        instance = self.get_local_instance(object_id, True)
        src_exec_env_id = instance._dc_meta.master_backend_id()
        if src_exec_env_id is not None:
            logger.debug("Found origin location %s", src_exec_env_id)
            if calling_backend_id is None or src_exec_env_id != calling_backend_id:
                # do not synchronize to calling source (avoid infinite loops)
                dest_backend = self.runtime.get_backend_client(src_exec_env_id)
                logger.debug(
                    "----> Propagating synchronization of %s to origin location %s",
                    object_id,
                    src_exec_env_id,
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
            logger.debug("Found replica locations %s", replica_locations)
            for replica_location in replica_locations:
                if calling_backend_id is None or replica_location != calling_backend_id:
                    # do not synchronize to calling source (avoid infinite loops)
                    dest_backend = self.runtime.get_backend_client(replica_location)
                    logger.debug(
                        "----> Propagating synchronization of %s to replica location %s",
                        object_id,
                        replica_location,
                    )
                    dest_backend.synchronize(
                        session_id,
                        object_id,
                        implementation_id,
                        serialized_value,
                        calling_backend_id=self.backend_id,
                    )
        logger.debug("----> Finished synchronization of %s", object_id)

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
                        logger.debug("Removing alias %s", instance._dc_alias)
                        self.self.runtime.delete_alias(instance)

                except Exception as ex:
                    traceback.print_exc()
                    logger.debug(
                        "Caught exception %s, Ignoring if object was not registered yet",
                        type(ex).__name__,
                    )
                    # ignore if object was not registered yet
                    pass
        except DataClayException as e:
            # TODO: better algorithm to avoid unfederation in wrong backend
            logger.debug(
                "Caught exception %s, Ignoring if object is not in current backend",
                type(e).__name__,
            )
        except Exception as e:
            logger.debug("Caught exception %s", type(e).__name__)
            raise e
        logger.debug("<--- Finished notification of unfederation")

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
