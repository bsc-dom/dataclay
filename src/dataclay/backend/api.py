""" Class description goes here. """

from __future__ import annotations

import asyncio
import logging
import pickle
import time
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Optional

from threadpoolctl import threadpool_limits

from dataclay import utils
from dataclay.config import set_runtime, settings
from dataclay.event_loop import dc_to_thread_io
from dataclay.exceptions import (
    DataClayException,
    DoesNotExistError,
    ObjectWithWrongBackendIdError,
    NoOtherBackendsAvailable
)
from dataclay.lock_manager import lock_manager
from dataclay.runtime import BackendRuntime
from dataclay.utils.serialization import dcdumps, dcloads, recursive_dcloads
from dataclay.utils.telemetry import trace

if TYPE_CHECKING:
    from uuid import UUID

    from dataclay.dataclay_object import DataClayObject

tracer = trace.get_tracer(__name__)
logger: logging.Logger = utils.LoggerEvent(logging.getLogger(__name__))


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
        self,
        object_id: UUID,
        method_name: str,
        args: tuple[Any],
        kwargs: dict[str, Any],
        exec_constraints: dict[str, Any],
    ) -> tuple[bytes, bool]:
        """Entry point for calling an active method of a DataClayObject"""

        logger.debug("(%s) Receiving remote call to activemethod '%s'", object_id, method_name)

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
            logger.warning("(%s) Wrong backend", object_id)
            await self.runtime.sync_object_metadata(instance)
            logger.warning(
                "(%s) Update backend to %s", object_id, instance._dc_meta.master_backend_id
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

        # Call activemethod in another thread
        logger.info("(%s) *** Starting activemethod '%s' in executor", object_id, method_name)
        max_threads = (
            None if exec_constraints.get("max_threads", 0) == 0 else exec_constraints["max_threads"]
        )
        logger.info("(%s) Max threads for activemethod: %s", object_id, max_threads)
        # TODO: Check that the threadpool_limit is not limiting our internal pool of threads.
        # like when we are serializing dataclay objects.
        with threadpool_limits(limits=max_threads):
            try:
                func = getattr(instance, method_name)
                if asyncio.iscoroutinefunction(func):
                    logger.debug("(%s) Awaiting activemethod coroutine", object_id)
                    result = await func(*args, **kwargs)
                else:
                    logger.debug("(%s) Running activemethod in new thread", object_id)
                    result = await dc_to_thread_io(func, *args, **kwargs)
            except Exception as e:
                # If an exception was raised, serialize it and return it to be raised by the client
                logger.info("(%s) *** Exception in activemethod '%s'", object_id, method_name)
                return pickle.dumps(e), True
        logger.info("(%s) *** Finished activemethod '%s' in executor", object_id, method_name)

        # Serialize the result if not None
        if result is not None:
            result = await dcdumps(result)

        return result, False

    # Store Methods

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
        logger.debug("(%s) Receiving remote call to __getattribute__ '%s'", object_id, attribute)
        instance = await self.runtime.get_object_by_id(object_id)
        if not instance._dc_is_local:
            logger.warning("(%s) Wrong backend", object_id)
            await self.runtime.sync_object_metadata(instance)
            logger.warning(
                "(%s) Update backend to %s", object_id, instance._dc_meta.master_backend_id
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
            value = await dc_to_thread_io(getattr, instance, attribute)
            return await dcdumps(value), False
        except Exception as e:
            return pickle.dumps(e), True

    @tracer.start_as_current_span("set_object_attribute")
    async def set_object_attribute(
        self, object_id: UUID, attribute: str, serialized_attribute: bytes
    ) -> tuple[bytes, bool]:
        """Updates an object attibute with ID provided"""
        logger.debug("(%s) Receiving remote call to __setattr__ '%s'", object_id, attribute)
        instance = await self.runtime.get_object_by_id(object_id)
        if not instance._dc_is_local:
            logger.warning("(%s) Wrong backend", object_id)
            await self.runtime.sync_object_metadata(instance)
            logger.warning(
                "(%s) Update backend to %s", object_id, instance._dc_meta.master_backend_id
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
            await dc_to_thread_io(setattr, instance, attribute, object_attribute)
            return None, False
        except Exception as e:
            return pickle.dumps(e), True

    @tracer.start_as_current_span("del_object_attribute")
    async def del_object_attribute(self, object_id: UUID, attribute: str) -> tuple[bytes, bool]:
        """Deletes an object attibute with ID provided"""
        logger.debug("(%s) Receiving remote call to __delattr__'%s'", object_id, attribute)
        instance = await self.runtime.get_object_by_id(object_id)
        if not instance._dc_is_local:
            logger.warning("(%s) Wrong backend", object_id)
            await self.runtime.sync_object_metadata(instance)
            logger.warning(
                "(%s) Update backend to %s", object_id, instance._dc_meta.master_backend_id
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
            await dc_to_thread_io(delattr, instance, attribute)
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
            raise NoOtherBackendsAvailable()

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
