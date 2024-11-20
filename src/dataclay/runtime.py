""" Class description goes here. """

from __future__ import annotations

import asyncio
import collections
import copy
import logging
import random
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID
from weakref import WeakValueDictionary

from dataclay import utils
from dataclay.config import exec_constraints_var, session_var, settings
from dataclay.data_manager import DataManager
from dataclay.dataclay_object import DataClayObject
from dataclay.exceptions import (
    DataClayException,
    ObjectIsNotVersionError,
    ObjectNotRegisteredError,
    ObjectWithWrongBackendIdError,
)
from dataclay.lock_manager import lock_manager
from dataclay.metadata.api import MetadataAPI
from dataclay.metadata.client import MetadataClient
from dataclay.utils.backend_clients import BackendClientsManager
from dataclay.utils.serialization import dcdumps, dcloads, recursive_dcdumps
from dataclay.utils.telemetry import trace

if TYPE_CHECKING:
    from collections.abc import Iterable

    from dataclay.metadata.kvdata import ObjectMetadata


tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)


class _DummyInmemoryHitsTotal:
    def inc(self):
        """Dummy function"""
        pass


class DataClayRuntime(ABC):
    def __init__(self, backend_id: UUID = None):
        # self._dataclay_id = None
        self.backend_id = backend_id
        self.is_backend = bool(backend_id)

        # Dictionary of all runtime memory objects stored as weakrefs.
        self.inmemory_objects: WeakValueDictionary[UUID, DataClayObject] = WeakValueDictionary()

        if settings.metrics:
            # pylint: disable=import-outside-toplevel
            from dataclay.utils import metrics

            metrics.dataclay_inmemory_objects.set_function(lambda: len(self.inmemory_objects))
            self.dataclay_inmemory_hits_total = metrics.dataclay_inmemory_hits_total
        else:
            self.dataclay_inmemory_hits_total = _DummyInmemoryHitsTotal()

    def start(self, metadata_service: MetadataAPI):
        # NOTE: Moved from __init__ to initialize the MetadataService in the dc_event_loop
        # this is restriction from Async gRPC
        # Initialize BackendClientsManager and Data Manager
        self.backend_clients = BackendClientsManager(metadata_service)
        self.data_manager = DataManager()
        self.backend_clients.start_update_loop()

        if self.is_backend:
            self.backend_clients.start_subscribe()
            self.data_manager.start_memory_monitor()

    ##############
    # Properties #
    ##############

    # Common runtime API

    async def make_persistent(
        self,
        instance: DataClayObject,
        alias: Optional[str] = None,
        backend_id: Optional[str] = None,
    ):
        """
        Persist an object and optionally its associated objects.

        Args:
            instance: The object to persist.
            alias: Optional alias for the object.
            backend_id: Optional ID of the destination backend.

        Returns:
            The ID of the backend where the object was persisted.
        """
        logger.debug(
            "(%s) Starting make_persistent. Alias=%s, backend_id=%s",
            instance._dc_meta.id,
            alias,
            backend_id,
        )

        # Check necessary for BackendAPI.new_object_version. This allows to set the dataset
        # before calling make_persistent, which is useful for registering a new version with
        # the same dataset as the original object.
        if instance._dc_meta.dataset_name is None:
            instance._dc_meta.dataset_name = session_var.get()["dataset_name"]

        # Register the alias
        if alias:
            logger.debug(
                "(%s) Registering alias '%s/%s'",
                instance._dc_meta.id,
                instance._dc_meta.dataset_name,
                alias,
            )
            await self.metadata_service.new_alias(
                alias, instance._dc_meta.dataset_name, instance._dc_meta.id
            )

        # If called inside backend runtime, default is to register in the current backend
        # unles another backend is explicitly specified
        if self.is_backend and (backend_id is None or backend_id == self.backend.id):
            logger.debug("(%s) Registering the object in this backend", instance._dc_meta.id)
            instance._dc_meta.master_backend_id = self.backend_id
            await self.metadata_service.upsert_object(instance._dc_meta)
            instance._dc_is_registered = True
            self.inmemory_objects[instance._dc_meta.id] = instance
            self.data_manager.add_hard_reference(instance)
            return self.backend_id

        # Called from client runtime, default is to choose a random backend
        elif backend_id is None:
            logger.debug(
                "(%s) Choosing a random backend to register the object", instance._dc_meta.id
            )
            # If there is no backend client, update the list of backend clients
            if not self.backend_clients:
                await self.backend_clients.update()
                if not self.backend_clients:
                    raise RuntimeError(
                        f"({instance._dc_meta.id}) No backends available to register the object"
                    )
            # Choose a random backend
            backend_id, backend_client = random.choice(tuple(self.backend_clients.items()))
        else:
            backend_client = await self.backend_clients.get(backend_id)

        # Serialize instance with a recursive Pickle
        visited_objects: dict[UUID, DataClayObject] = {}
        serialized_objects = await recursive_dcdumps(
            instance, local_objects=visited_objects, make_persistent=True
        )
        # Register the object in the backend
        await backend_client.make_persistent(serialized_objects)

        # Update the object metadata
        for dc_object in visited_objects.values():
            dc_object._clean_dc_properties()
            dc_object._dc_is_registered = True
            dc_object._dc_is_local = False
            dc_object._dc_is_loaded = False
            dc_object._dc_meta.master_backend_id = backend_id
            self.inmemory_objects[dc_object._dc_meta.id] = dc_object

        return instance._dc_meta.master_backend_id

    ##################
    # Object methods #
    ##################

    async def get_object_by_id(
        self, object_id: UUID, object_md: Optional[ObjectMetadata] = None
    ) -> DataClayObject:
        """Get dataclay object from inmemory_objects. If not present, get object metadata
        and create new proxy object.
        """
        logger.debug("(%s) Getting dataclay object by id", object_id)

        try:
            dc_object = self.inmemory_objects[object_id]
            self.dataclay_inmemory_hits_total.inc()
            logger.debug("(%s) Object found in inmemory_objects", object_id)
            return dc_object
        except KeyError:
            async with lock_manager.get_lock(object_id).writer_lock:
                try:
                    dc_object = self.inmemory_objects[object_id]
                    self.dataclay_inmemory_hits_total.inc()
                    return dc_object
                except KeyError:
                    # When the object is not in the inmemory_objects,
                    # we get the object metadata from kvstore, and create a new proxy
                    # object from it.

                    logger.debug("(%s) Object not found in inmemory_objects", object_id)

                    # If object metadata is not provided, get it from the metadata service
                    if object_md is None:
                        logger.debug("(%s) Getting object metadata from MDS", object_id)
                        object_md = await self.metadata_service.get_object_md_by_id(object_id)

                    # Create a new proxy object
                    cls: DataClayObject = utils.get_class_by_name(object_md.class_name)
                    proxy_object = cls.new_proxy_object()
                    proxy_object._dc_meta = object_md

                    # Determine if the object is local, replica, or remote
                    if proxy_object._dc_meta.master_backend_id == self.backend_id:
                        proxy_object._dc_is_local = True
                        assert self.backend_id not in proxy_object._dc_meta.replica_backend_ids
                    elif self.backend_id in proxy_object._dc_meta.replica_backend_ids:
                        proxy_object._dc_is_local = True
                        proxy_object._dc_is_replica = True
                    else:
                        proxy_object._dc_is_local = False

                    # Set the object as registered and not loaded
                    proxy_object._dc_is_loaded = False
                    proxy_object._dc_is_registered = True

                    # Since the object is not loaded, don't store a hard reference
                    # only add th object to the inmemory list
                    # The object will be loaded if needed (and if local) by calling `load_object`
                    # TODO: If the gc deletes the proxy object very quickly, it may be inefficient
                    # if many calls are made to the same object, and this is deleted every time.
                    # TODO: Check if this is really the case. If so, gc should act in a LIFO way.
                    self.inmemory_objects[proxy_object._dc_meta.id] = proxy_object
                    logger.debug(
                        "(%s) Proxy object created and added to inmemory_objects", object_id
                    )
                    return proxy_object

    async def get_object_by_alias(self, alias: str, dataset_name: str = None) -> DataClayObject:
        """Get object instance from alias"""
        logger.debug("Getting object by alias %s", alias)
        if dataset_name is None:
            dataset_name = session_var.get()["dataset_name"]
        object_md = await self.metadata_service.get_object_md_by_alias(alias, dataset_name)
        return await self.get_object_by_id(object_md.id, object_md)

    async def get_object_properties(self, instance: DataClayObject) -> dict[str, Any]:
        logger.debug("(%s) Getting object properties", instance._dc_meta.id)
        if instance._dc_is_local:
            if not instance._dc_is_loaded:
                await self.data_manager.load_object(instance)
            return instance._dc_properties
        else:
            backend_client = await self.backend_clients.get(instance._dc_meta.master_backend_id)
            serialized_properties = await backend_client.get_object_properties(instance._dc_meta.id)
            return await dcloads(serialized_properties)

    async def make_object_copy(
        self, instance: DataClayObject, recursive: bool = False, is_proxy: bool = False
    ):
        logger.debug("(%s) Making object copy", instance._dc_meta.id)
        object_properties = copy.deepcopy(await self.get_object_properties(instance))
        if is_proxy:
            # Avoid the object get persistent automatically when called in a backend
            # Needed for new_version
            object_copy = instance.__class__.new_proxy_object()
        else:
            object_copy = DataClayObject.__new__(instance.__class__)
        vars(object_copy).update(object_properties)
        return object_copy

    async def proxify_object(self, instance: DataClayObject, new_object_id: UUID):
        logger.debug("(%s) Proxifying object to %s", instance._dc_meta.id, new_object_id)
        if not instance._dc_is_registered:
            raise ObjectNotRegisteredError(instance._dc_meta.id)

        if instance._dc_is_local:
            assert self.is_backend
            async with lock_manager.get_lock(instance._dc_meta.id).writer_lock:
                # TODO: remove pickle file if serialized in disk (when not loaded)
                instance._clean_dc_properties()
                instance._dc_is_loaded = False
                instance._dc_is_local = False
                self.data_manager.remove_hard_reference(instance)
                # NOTE: There is no need to delete, and it may be good
                # in case that an object was serialized to disk before a
                # consolidation. However, it will be deleted also since
                # inmemory_objects is a weakref dict.
                # del self.inmemory_objects[instance._dc_meta.id]
                await self.metadata_service.delete_object(instance._dc_meta.id)
        else:
            backend_client = await self.backend_clients.get(instance._dc_meta.master_backend_id)
            await backend_client.proxify_object(instance._dc_meta.id, new_object_id)

        instance._dc_meta.id = new_object_id

    async def change_object_id(self, instance: DataClayObject, new_object_id: UUID):
        logger.debug("(%s) Changing object id to %s", instance._dc_meta.id, new_object_id)
        old_object_id = instance._dc_meta.id

        if instance._dc_is_local:
            async with lock_manager.get_lock(instance._dc_meta.id).writer_lock:
                # loaded since pickle filed is named with the old object_id
                if not instance._dc_is_loaded:
                    await self.data_manager.load_object(instance)

                # update the loaded_objects with the new object_id
                self.data_manager.remove_hard_reference(instance)
                instance._dc_meta.id = new_object_id
                self.data_manager.add_hard_reference(instance)

                self.inmemory_objects[new_object_id] = instance
                await self.metadata_service.change_object_id(old_object_id, new_object_id)
                # HACK: The only use case for change_object_id is to consolidate, therefore:
                instance._dc_meta.original_object_id = None
                instance._dc_meta.versions_object_ids = []
                await self.metadata_service.upsert_object(instance._dc_meta)
        else:
            backend_client = await self.backend_clients.get(instance._dc_meta.master_backend_id)
            await backend_client.change_object_id(instance._dc_meta.id, new_object_id)
            instance._dc_meta.id = new_object_id

        del self.inmemory_objects[old_object_id]

    async def sync_object_metadata(self, instance: DataClayObject):
        logger.debug("(%s) Syncing object metadata", instance._dc_meta.id)
        if not instance._dc_is_registered:
            raise ObjectNotRegisteredError(instance._dc_meta.id)
        object_md = await self.metadata_service.get_object_md_by_id(instance._dc_meta.id)
        instance._dc_meta = object_md

    ##################
    # Active Methods #
    ##################

    async def call_remote_method(
        self, instance: DataClayObject, method_name: str, args: tuple, kwargs: dict
    ):
        with tracer.start_as_current_span("call_remote_method") as span:
            span.set_attribute("class", str(instance._dc_meta.class_name))
            span.set_attribute("method", str(method_name))
            span.set_attribute("args", str(args))
            span.set_attribute("kwargs", str(kwargs))

            logger.debug(
                "(%s) Calling remote method %s args=%s, kwargs=%s",
                instance._dc_meta.id,
                method_name,
                args,
                kwargs,
            )

            # Serialize args and kwargs
            serialized_args, serialized_kwargs = await asyncio.gather(
                dcdumps(args), dcdumps(kwargs)
            )

            # Fault tolerance loop
            num_retries = 0
            while True:
                num_retries += 1
                logger.debug("(%s) Attempt %s", instance._dc_meta.id, num_retries)
                # Get the intersection between backend clients and object backends
                avail_backends = instance._dc_all_backend_ids.intersection(
                    self.backend_clients.keys()
                )

                # If the intersection is empty (no backends available), update the list of backend
                # clients and the object backend locations, and try again...
                if not avail_backends:
                    logger.warning("(%s) No backends available. Syncing...", instance._dc_meta.id)
                    await asyncio.gather(self.backend_clients.update(), instance.a_sync())

                    avail_backends = instance._dc_all_backend_ids.intersection(
                        self.backend_clients.keys()
                    )
                    if not avail_backends:
                        raise RuntimeError(
                            f"({instance._dc_meta.id}) No backends available to call activemethod"
                        )

                # Choose a random backend from the available ones
                backend_id = random.choice(tuple(avail_backends))
                backend_client = await self.backend_clients.get(backend_id)
                logger.debug("(%s) Backend %s chosen", instance._dc_meta.id, backend_id)

                # If the connection fails, update the list of backend clients, and try again
                try:
                    if method_name == "__getattribute__":
                        logger.debug(
                            "(%s) Getting remote attribute '%s'", instance._dc_meta.id, args[0]
                        )
                        (
                            serialized_response,
                            is_exception,
                        ) = await backend_client.get_object_attribute(
                            instance._dc_meta.id,
                            args[0],  # attribute name
                        )
                    elif method_name == "__setattr__":
                        logger.debug(
                            "(%s) Setting remote attribute '%s'", instance._dc_meta.id, args[0]
                        )
                        (
                            serialized_response,
                            is_exception,
                        ) = await backend_client.set_object_attribute(
                            instance._dc_meta.id,
                            args[0],  # attribute name
                            await dcdumps(args[1]),  # attribute value
                        )
                    elif method_name == "__delattr__":
                        logger.debug(
                            "(%s) Deleting remote attribute '%s'", instance._dc_meta.id, args[0]
                        )
                        (
                            serialized_response,
                            is_exception,
                        ) = await backend_client.del_object_attribute(
                            instance._dc_meta.id,
                            args[0],  # attribute name
                        )
                    else:
                        logger.debug(
                            "(%s) Executing remote method '%s' with constraints %s",
                            instance._dc_meta.id,
                            method_name,
                            exec_constraints_var.get(),
                        )
                        serialized_response, is_exception = await backend_client.call_active_method(
                            object_id=instance._dc_meta.id,
                            method_name=method_name,
                            args=serialized_args,
                            kwargs=serialized_kwargs,
                            exec_constraints=exec_constraints_var.get(),
                        )
                except DataClayException as e:
                    if "failed to connect" in str(e):
                        logger.warning("(%s) Connection failed. Retrying...", instance._dc_meta.id)
                        await self.backend_clients.update()
                        continue
                    else:
                        raise e

                # Deserialize the response if not None
                if serialized_response:
                    logger.debug("(%s) Deserializing response", instance._dc_meta.id)
                    response = await dcloads(serialized_response)
                else:
                    logger.debug("(%s) Response is None", instance._dc_meta.id)
                    response = None

                # If response is ObjectWithWrongBackendIdError, update object metadata and retry
                if isinstance(response, ObjectWithWrongBackendIdError):
                    logger.warning(
                        "(%s) Object with wrong backend id. Retrying...", instance._dc_meta.id
                    )
                    instance._dc_meta.master_backend_id = response.backend_id
                    instance._dc_meta.replica_backend_ids = response.replica_backend_ids
                    continue

                # If the response is an exception, it is raised
                if is_exception:
                    logger.debug(
                        "(%s) Remote method '%s' raised an exception",
                        instance._dc_meta.id,
                        method_name,
                    )
                    raise response

                logger.debug(
                    "(%s) Remote method '%s' executed successfully",
                    instance._dc_meta.id,
                    method_name,
                )
                return response

    #########
    # Alias #
    #########

    async def add_alias(self, instance: DataClayObject, alias: str):
        logger.debug("(%s) Adding alias %s", instance._dc_meta.id, alias)
        if not instance._dc_is_registered:
            raise ObjectNotRegisteredError(instance._dc_meta.id)
        if not alias:
            raise AttributeError("Alias cannot be None or empty string")
        await self.metadata_service.new_alias(
            alias, instance._dc_meta.dataset_name, instance._dc_meta.id
        )

    async def delete_alias(self, alias: str, dataset_name: Optional[str] = None):
        logger.debug("Deleting alias %s.%s", dataset_name, alias)
        if dataset_name is None:
            dataset_name = session_var.get()["dataset_name"]
        await self.metadata_service.delete_alias(alias, dataset_name)

    async def get_all_alias(
        self, dataset_name: Optional[str] = None, object_id: Optional[UUID] = None
    ):
        logger.debug("Getting all alias for dataset %s and object %s", dataset_name, object_id)
        return await self.metadata_service.get_all_alias(dataset_name, object_id)

    #################
    # Store Methods #
    #################

    async def send_objects(
        self,
        instances: Iterable[DataClayObject],
        backend_id: UUID,
        make_replica: bool,
        recursive: bool = False,
        remotes: bool = True,
    ):
        """Send DataClay instances from one backend to another.

        The instances must be registered in the metadata service.
        It can be used for moving objects (changing _dc_meta.master_backend_id)
        or for creating remotes (appending to _dc_meta.replica_backend_ids)

        If recursive=True, all references from the objects will also be sent.
        If recursice=True and remotes=False, local references will be sent, but
        not remote references.
        """
        logger.debug(
            "Send (%s) objects to backend %s. Make replica=%s, recursive=%s, remotes=%s",
            len(instances),
            backend_id,
            make_replica,
            recursive,
            remotes,
        )

        # NOTE: We cannot make a replica of a replica because we need a global lock
        # of the metadata to keep consistency of _dc_meta.replica_backend_ids. Therefore,
        # we only allow to make replicas of master objects, which will acquire a lock
        # when updating the metadata.

        visited_local_objects = {}
        pending_remote_objects = {}
        serialized_local_objects = []

        # Process each instance and serialize
        for instance in instances:
            if instance._dc_is_local and not instance._dc_is_replica:
                # Check if the instance was already visited (as a reference of another instance)
                if instance._dc_meta.id in visited_local_objects:
                    continue

                # Add the instance to the visited objects
                visited_local_objects[instance._dc_meta.id] = instance

                # Load the object if it is not loaded
                if not instance._dc_is_loaded:
                    await self.data_manager.load_object(instance)

                if recursive:
                    if remotes:
                        # If recursive and remotes, we need to obtain the remote references
                        serialized_objects = await recursive_dcdumps(
                            instance, visited_local_objects, pending_remote_objects
                        )
                    else:
                        serialized_objects = await recursive_dcdumps(
                            instance, visited_local_objects
                        )
                    serialized_local_objects.extend(serialized_objects)
                else:
                    # If not recursive, we only serialize the current instance
                    object_bytes = await dcdumps(instance._dc_state)
                    serialized_local_objects.append(object_bytes)
            else:
                # If the instance is not local, then it is remote
                pending_remote_objects[instance._dc_meta.id] = instance

        # Register the objects in the destination backend
        # NOTE: Could be that the backend_id is the same as the current backend
        # This could be useful to move all references together in the same backend
        if len(serialized_local_objects) > 0 and backend_id != self.backend_id:
            backend_client = await self.backend_clients.get(backend_id)
            await backend_client.register_objects(
                serialized_local_objects, make_replica=make_replica
            )
            # Update the metadata of the local objects
            for local_object in visited_local_objects.values():
                if make_replica:
                    local_object._dc_meta.replica_backend_ids.add(backend_id)
                else:
                    # Object has been moved to another backend
                    # The object is no longer local, and is a proxy
                    # TODO: Remove pickle file to reduce space
                    self.data_manager.remove_hard_reference(local_object)
                    local_object._clean_dc_properties()
                    local_object._dc_is_local = False
                    local_object._dc_is_loaded = False
                    local_object._dc_meta.master_backend_id = backend_id
                    local_object._dc_meta.replica_backend_ids.discard(backend_id)

        # Update the metadata of the remote proxy objects
        counter = collections.Counter()
        for remote_object in pending_remote_objects.values():
            # Count the number of objects per backend
            counter[remote_object._dc_meta.master_backend_id] += 1
            if make_replica:
                if backend_id != remote_object._dc_meta.master_backend_id:
                    remote_object._dc_meta.replica_backend_ids.add(backend_id)
            else:
                remote_object._dc_meta.master_backend_id = backend_id
                remote_object._dc_meta.replica_backend_ids.discard(backend_id)

        # This should not happen
        assert counter[self.backend_id] == 0

        # Ask to the backend with most remote objects to continue the "send_objects" operation
        # This is done to reduce the number of recursive "send_objects" calls between backends
        if len(counter) > 0:
            remote_backend_id = counter.most_common(1)[0][0]
            remote_backend_client = await self.backend_clients.get(remote_backend_id)
            await remote_backend_client.send_objects(
                pending_remote_objects.keys(), backend_id, make_replica, recursive, remotes
            )

    async def replace_object_properties(
        self, instance: DataClayObject, new_instance: DataClayObject
    ):
        logger.debug("(%s) Replacing object properties", instance._dc_meta.id)
        new_object_properties = await self.get_object_properties(new_instance)
        await self.update_object_properties(instance, new_object_properties)

    async def update_object_properties(
        self, instance: DataClayObject, new_properties: dict[str, Any]
    ):
        logger.debug("(%s) Updating object properties", instance._dc_meta.id)

        if instance._dc_is_local:
            if not instance._dc_is_loaded:
                await self.data_manager.load_object(instance)
            vars(instance).update(new_properties)
        else:
            backend_client = await self.backend_clients.get(instance._dc_meta.master_backend_id)
            await backend_client.update_object_properties(
                instance._dc_meta.id, await dcdumps(new_properties)
            )

    async def new_object_version(self, instance: DataClayObject, backend_id: Optional[UUID] = None):
        logger.debug("(%s) Creating new version", instance._dc_meta.id)

        # Create a proxy copy of the object
        new_version = await self.make_object_copy(instance, is_proxy=True)

        # Set the original object ID and the versions to the new version
        if instance._dc_meta.original_object_id is None:
            new_version._dc_meta.original_object_id = instance._dc_meta.id
        else:
            new_version._dc_meta.original_object_id = instance._dc_meta.original_object_id
            new_version._dc_meta.versions_object_ids = instance._dc_meta.versions_object_ids + [
                instance._dc_meta.id
            ]

        # Copy the dataset name to the new version
        new_version._dc_meta.dataset_name = instance._dc_meta.dataset_name

        # Register and return the new version
        await self.make_persistent(new_version, backend_id=backend_id)
        return new_version

    async def consolidate_version(self, instance: DataClayObject):
        logger.debug("(%s) Consolidating version", instance._dc_meta.id)

        # Check if the object is a version
        if instance._dc_meta.original_object_id is None:
            raise ObjectIsNotVersionError(instance._dc_meta.id)

        original_object_id = instance._dc_meta.original_object_id

        # Proxify all versions
        for version_object_id in instance._dc_meta.versions_object_ids:
            version = await self.get_object_by_id(version_object_id)
            await self.proxify_object(version, original_object_id)

        # Proxify original object and steal its ID to the instance
        original_object = await self.get_object_by_id(original_object_id)
        await self.proxify_object(original_object, original_object_id)
        await self.change_object_id(instance, original_object_id)

        # Clean version metadata
        instance._dc_meta.original_object_id = None
        instance._dc_meta.versions_object_ids = []

    ############
    # Replicas #
    ############

    async def new_object_replica(
        self,
        instance: DataClayObject,
        backend_id: Optional[UUID] = None,
        recursive: bool = False,
        remotes: bool = True,
    ):
        logger.debug("(%s) Creating new replica", instance._dc_meta.id)

        if not instance._dc_is_registered:
            raise ObjectNotRegisteredError(instance._dc_meta.id)

        if backend_id is None:
            # Get the backends that do not have a replica of the object
            avail_backends = set(self.backend_clients.keys()) - instance._dc_all_backend_ids

            # If there is no backend without a replica, update the list of backend clients,
            # sync the object metadata, and try again
            if not avail_backends:
                await self.backend_clients.update()
                await instance.a_sync()
                avail_backends = set(self.backend_clients.keys()) - instance._dc_all_backend_ids

                if not avail_backends:
                    logger.warning("All available backends have a replica")
                    if not recursive:
                        # If not recursive, no need to continue
                        return
                    else:
                        # If recursive, we still continue in order to send the instance referees
                        avail_backends = self.backend_clients.keys()

            # Choose a random backend from the available ones
            backend_id = random.choice(tuple(avail_backends))

        elif backend_id in instance._dc_meta.replica_backend_ids:
            # If the backend already have a replica, sync the instnace metadata, and try again
            await instance.a_sync()
            if backend_id in instance._dc_meta.replica_backend_ids:
                logger.warning("The backend already have a replica")
                # If not recursive, no need to continue
                if not recursive:
                    return

        await self.send_objects([instance], backend_id, True, recursive, remotes)

    ############
    # Shutdown #
    ############

    @abstractmethod
    async def stop(self):
        pass

    # NOTE: Previous commits contained deprecated replica, federation, tracing/extrae methods


class ClientRuntime(DataClayRuntime):
    def __init__(self, metadata_service_host: str, metadata_service_port: int):
        self.metadata_host = metadata_service_host
        self.metadata_port = metadata_service_port
        super().__init__()

    async def start(self):
        # NOTE: Moved from __init__ to initialize the MetadataService in the dc_event_loop
        # this is restriction from Async gRPC
        self.metadata_service = MetadataClient(self.metadata_host, self.metadata_port)
        super().start(self.metadata_service)

    async def stop(self):
        await self.backend_clients.stop()
        await self.metadata_service.close()


class BackendRuntime(DataClayRuntime):
    def __init__(self, kv_host: str, kv_port: int, backend_id: UUID):
        self.metadata_host = kv_host
        self.metadata_port = kv_port
        # Initialize Metadata Service
        super().__init__(backend_id)
        self.backend_id = backend_id
        # NOTE: Backend is already running in dc_event_loop, no need to divide
        self.metadata_service = MetadataAPI(self.metadata_host, self.metadata_port)
        super().start(self.metadata_service)

    async def stop(self):
        # Stop all backend clients
        await self.backend_clients.stop()

        # Remove backend entry from metadata
        await self.metadata_service.delete_backend(self.backend_id)

        # Stop DataManager memory monitor
        self.data_manager.stop_memory_monitor()

        # Flush all data if not ephemeral
        if not settings.ephemeral:
            await self.data_manager.flush_all()

        # Stop metadata redis connection
        await self.metadata_service.close()
