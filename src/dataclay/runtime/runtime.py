""" Class description goes here. """
from __future__ import annotations

import collections
import concurrent.futures
import copy
import logging
import pickle
import random
import threading
import time
from abc import ABC, abstractmethod
from builtins import Exception
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID
from weakref import WeakValueDictionary

from dataclay import utils
from dataclay.backend.client import BackendClient
from dataclay.config import settings
from dataclay.dataclay_object import DataClayObject
from dataclay.exceptions import *
from dataclay.runtime import LockManager
from dataclay.utils import metrics
from dataclay.utils.serialization import dcdumps, recursive_dcdumps
from dataclay.utils.telemetry import trace

if TYPE_CHECKING:
    from collections.abc import Iterable

    from dataclay.backend.data_manager import DataManager
    from dataclay.metadata.api import MetadataAPI
    from dataclay.metadata.client import MetadataClient
    from dataclay.metadata.kvdata import Backend, ObjectMetadata, Session


tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)


class BackendClientsMonitor(threading.Thread):
    """Thread that periodically updates the backend clients."""

    def __init__(self, runtime: DataClayRuntime):
        threading.Thread.__init__(self, name="backend-clients-monitor")
        self.daemon = True
        self.runtime = runtime

    def run(self):
        while True:
            logger.debug("Updating backend clients")
            self.runtime.update_backend_clients()
            time.sleep(settings.backend_clients_check_interval)


class DataClayRuntime(ABC):
    def __init__(self, metadata_service: MetadataAPI | MetadataClient, backend_id: UUID = None):
        # self._dataclay_id = None
        self.backend_id = backend_id
        self.is_backend = bool(backend_id)
        self.metadata_service = metadata_service

        self.backend_clients: dict[UUID, BackendClient] = {}
        self.backend_clients_monitor = BackendClientsMonitor(self)
        self.backend_clients_monitor.start()

        # Memory objects. This dictionary must contain all objects in runtime memory (client or server), as weakrefs.
        self.inmemory_objects: WeakValueDictionary[UUID, DataClayObject] = WeakValueDictionary()
        metrics.dataclay_inmemory_objects.set_function(lambda: len(self.inmemory_objects))

    ##############
    # Properties #
    ##############

    @property
    @abstractmethod
    def session(self) -> Session:
        pass

    # Common runtime API

    def make_persistent(
        self,
        instance: DataClayObject,
        alias: Optional[str] = None,
        backend_id: Optional[str] = None,
    ):
        """This method creates a new Persistent Object using the provided stub
        instance and, if indicated, all its associated objects also Logic module API used for communication
        This function is called from a stub/execution class

        Args:
            instance: Instance to make persistent
            backend_id: Indicates which is the destination backend
            alias: Alias for the object

        Returns:
            ID of the backend in which the object was persisted.
        """
        logger.debug("(%s) Starting make_persistent", instance._dc_meta.id)

        if instance._dc_is_registered:
            raise ObjectAlreadyRegisteredError(instance._dc_meta.id)

        # Check necessary for BackendAPI.new_object_version. This allows to set the dataset
        # before calling make_persistent, which is useful for registering a new verion with
        # the same dataset as the original object.
        if instance._dc_meta.dataset_name is None:
            instance._dc_meta.dataset_name = self.session.dataset_name

        if alias:
            self.metadata_service.new_alias(alias, self.session.dataset_name, instance._dc_meta.id)

        # If calling make_persistent in a backend, the default is to register the object
        # in the current backend, unles another backend is specified
        if self.is_backend and (backend_id is None or backend_id == self.backend.id):
            instance._dc_meta.master_backend_id = self.backend_id
            self.metadata_service.upsert_object(instance._dc_meta)
            instance._dc_is_registered = True
            self.inmemory_objects[instance._dc_meta.id] = instance
            self.data_manager.add_hard_reference(instance)
            return self.backend_id

        elif backend_id is None:
            # If there is no backend client, update the list of backend clients
            if not self.backend_clients:
                self.update_backend_clients()
                if not self.backend_clients:
                    raise RuntimeError(
                        f"({instance._dc_meta.id}) No backends available to make persistent"
                    )
            backend_id, backend_client = random.choice(tuple(self.backend_clients.items()))
        else:
            backend_client = self.get_backend_client(backend_id)

        # Serialize instance with Pickle
        visited_objects: dict[UUID, DataClayObject] = {}
        serialized_objects = recursive_dcdumps(
            instance, local_objects=visited_objects, make_persistent=True
        )
        backend_client.make_persistent(serialized_objects)

        for dc_object in visited_objects.values():
            dc_object._clean_dc_properties()
            dc_object._dc_is_registered = True
            dc_object._dc_is_local = False
            dc_object._dc_is_loaded = False
            dc_object._dc_meta.master_backend_id = backend_id
            self.inmemory_objects[dc_object._dc_meta.id] = dc_object

        return instance._dc_meta.master_backend_id

    @property
    @abstractmethod
    def data_manager(self) -> DataManager:
        pass

    ##################
    # Object methods #
    ##################

    # TODO: Check if is taking the metrics from KeyError, if not put inside
    @metrics.dataclay_inmemory_misses_total.count_exceptions(KeyError)
    def get_object_by_id(self, object_id: UUID, object_md: ObjectMetadata = None) -> DataClayObject:
        """Get dataclay object from inmemory_objects. If not present, get object metadata
        and create new proxy object.
        """
        logger.debug("(%s) Get object by id", object_id)

        try:
            dc_object = self.inmemory_objects[object_id]
            metrics.dataclay_inmemory_hits_total.inc()
            return dc_object
        except KeyError:
            with LockManager.write(object_id):
                try:
                    dc_object = self.inmemory_objects[object_id]
                    metrics.dataclay_inmemory_hits_total.inc()
                    return dc_object
                except KeyError:
                    # NOTE: When the object is not in the inmemory_objects,
                    # we get the object metadata from etcd, and create a new proxy
                    # object from it.

                    if object_md is None:
                        object_md = self.metadata_service.get_object_md_by_id(object_id)

                    cls: DataClayObject = utils.get_class_by_name(object_md.class_name)

                    proxy_object = cls.new_proxy_object()
                    proxy_object._dc_meta = object_md

                    if proxy_object._dc_meta.master_backend_id == self.backend_id:
                        proxy_object._dc_is_local = True
                        assert self.backend_id not in proxy_object._dc_meta.replica_backend_ids
                    elif self.backend_id in proxy_object._dc_meta.replica_backend_ids:
                        proxy_object._dc_is_local = True
                        proxy_object._dc_is_replica = True
                    else:
                        proxy_object._dc_is_local = False

                    proxy_object._dc_is_loaded = False
                    proxy_object._dc_is_registered = True

                    # Since it is no loaded, we only add it to the inmemory list
                    # The object will be loaded if needed calling `load_object`
                    self.inmemory_objects[proxy_object._dc_meta.id] = proxy_object
                    return proxy_object

    def get_object_by_alias(self, alias: str, dataset_name: str = None) -> DataClayObject:
        """Get object instance from alias"""
        if dataset_name is None:
            dataset_name = self.session.dataset_name

        object_md = self.metadata_service.get_object_md_by_alias(alias, dataset_name)

        return self.get_object_by_id(object_md.id, object_md)

    def get_object_properties(self, instance: DataClayObject) -> dict[str, Any]:
        if instance._dc_is_local:
            if not instance._dc_is_loaded:
                self.data_manager.load_object(instance)
            return instance._dc_properties
        else:
            backend_client = self.get_backend_client(instance._dc_meta.master_backend_id)
            serialized_properties = backend_client.get_object_properties(instance._dc_meta.id)
            return pickle.loads(serialized_properties)

    def make_object_copy(
        self, instance: DataClayObject, recursive: bool = False, is_proxy: bool = False
    ):
        object_properties = copy.deepcopy(self.get_object_properties(instance))
        if is_proxy:
            # Avoid the object get persistent automatically when called in a backend
            # Needed for new_version
            object_copy = instance.__class__.new_proxy_object()
        else:
            object_copy = DataClayObject.__new__(instance.__class__)
        vars(object_copy).update(object_properties)
        return object_copy

    def proxify_object(self, instance: DataClayObject, new_object_id: UUID):
        if not instance._dc_is_registered:
            raise ObjectNotRegisteredError(instance._dc_meta.id)

        if instance._dc_is_local:
            assert self.is_backend
            with LockManager.write(instance._dc_meta.id):
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
                self.metadata_service.delete_object(instance._dc_meta.id)
        else:
            backend_client = self.get_backend_client(instance._dc_meta.master_backend_id)
            backend_client.proxify_object(instance._dc_meta.id, new_object_id)

        instance._dc_meta.id = new_object_id

    def change_object_id(self, instance: DataClayObject, new_object_id: UUID):
        old_object_id = instance._dc_meta.id

        if instance._dc_is_local:
            with LockManager.write(instance._dc_meta.id):
                # loaded since pickle filed is named with the old object_id
                if not instance._dc_is_loaded:
                    self.data_manager.load_object(instance)

                # update the loaded_objects with the new object_id
                self.data_manager.remove_hard_reference(instance)
                instance._dc_meta.id = new_object_id
                self.data_manager.add_hard_reference(instance)

                self.inmemory_objects[new_object_id] = instance
                self.metadata_service.change_object_id(old_object_id, new_object_id)
                # HACK: The only use case for change_object_id is to consolidate, therefore:
                instance._dc_meta.original_object_id = None
                instance._dc_meta.versions_object_ids = []
                self.metadata_service.upsert_object(instance._dc_meta)
        else:
            backend_client = self.get_backend_client(instance._dc_meta.master_backend_id)
            backend_client.change_object_id(instance._dc_meta.id, new_object_id)
            instance._dc_meta.id = new_object_id

        del self.inmemory_objects[old_object_id]

    def sync_object_metadata(self, instance: DataClayObject):
        if not instance._dc_is_registered:
            raise ObjectNotRegisteredError(instance._dc_meta.id)
        object_md = self.metadata_service.get_object_md_by_id(instance._dc_meta.id)
        instance._dc_meta = object_md

    ##################
    # Active Methods #
    ##################

    def call_remote_method(
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
            serialized_args = dcdumps(args)
            serialized_kwargs = dcdumps(kwargs)

            # Fault tolerance loop
            while True:
                # Get the intersection between backend clients and object backends
                avail_backends = instance._dc_all_backend_ids.intersection(
                    self.backend_clients.keys()
                )

                # If the intersection is empty (no backends available), update the list of backend
                # clients and the object backend locations, and try again
                if not avail_backends:
                    logger.warning("(%s) No backends available. Syncing...", instance._dc_meta.id)
                    self.update_backend_clients()
                    instance.sync()
                    avail_backends = instance._dc_all_backend_ids.intersection(
                        self.backend_clients.keys()
                    )
                    if not avail_backends:
                        raise RuntimeError(
                            f"({instance._dc_meta.id}) No backends available to call activemethod"
                        )

                # Choose a random backend from the available ones
                backend_id = random.choice(tuple(avail_backends))
                backend_client = self.get_backend_client(backend_id)

                # If the connection fails, update the list of backend clients, and try again
                try:
                    if method_name == "__getattribute__":
                        logger.debug(
                            "The backend is %s with backend client %s", backend_id, backend_client
                        )
                        serialized_response, is_exception = backend_client.get_object_attribute(
                            instance._dc_meta.id,
                            args[0],  # attribute name
                        )
                    elif method_name == "__setattr__":
                        backend_client.set_object_attribute(
                            instance._dc_meta.id,
                            args[0],  # attribute name
                            dcdumps(args[1]),  # attribute value
                        )
                        serialized_response = None
                        is_exception = False
                    else:
                        serialized_response, is_exception = backend_client.call_active_method(
                            self.session.id,
                            instance._dc_meta.id,
                            method_name,
                            serialized_args,
                            serialized_kwargs,
                        )
                except DataClayException as e:
                    if "failed to connect" in str(e):
                        logger.warning("(%s) Failed to connect. Syncing...", instance._dc_meta.id)
                        self.update_backend_clients()
                        continue
                    else:
                        raise e

                if serialized_response:
                    response = pickle.loads(serialized_response)

                    # If the response is an ObjectWithWrongBackendIdError, update the object metadata
                    # and try again
                    if isinstance(response, ObjectWithWrongBackendIdError):
                        instance._dc_meta.master_backend_id = response.backend_id
                        instance._dc_meta.replica_backend_ids = response.replica_backend_ids
                        continue

                    # If the response is and exception, raise it. Correct workflow.
                    # NOTE: The exception was raised inside the active method
                    if is_exception:
                        raise response

                    return response

                else:
                    # Void active method returns None
                    return None

    #########
    # Alias #
    #########

    def add_alias(self, instance: DataClayObject, alias: str):
        if not instance._dc_is_registered:
            raise ObjectNotRegisteredError(instance._dc_meta.id)
        if not alias:
            raise AttributeError("Alias cannot be None or empty string")
        self.metadata_service.new_alias(alias, instance._dc_meta.dataset_name, instance._dc_meta.id)

    def delete_alias(self, alias: str, dataset_name: Optional[str] = None):
        if dataset_name is None:
            dataset_name = self.session.dataset_name

        self.metadata_service.delete_alias(alias, dataset_name, self.session.id)

    def get_all_alias(self, dataset_name: Optional[str] = None, object_id: Optional[UUID] = None):
        return self.metadata_service.get_all_alias(dataset_name, object_id)

    ############
    # Backends #
    ############

    def get_backend_client(self, backend_id: UUID) -> BackendClient:
        try:
            return self.backend_clients[backend_id]
        except KeyError:
            pass

        self.update_backend_clients()
        return self.backend_clients[backend_id]

    def reload_backend_clients(self):
        """Same as update_backend_clients, but to be used when not wanting to check channel readdinnes"""
        backend_infos = self.metadata_service.get_all_backends(from_backend=self.is_backend)
        new_backend_clients = {}

        for backend_id, backend_info in backend_infos.items():
            # Check if the backend is already in the backend_clients
            if backend_id in self.backend_clients:
                # Check if the backend location is the same
                # Don't check if the backend is ready, since the metadata has already check it
                if (
                    backend_info.host == self.backend_clients[backend_id].host
                    and backend_info.port == self.backend_clients[backend_id].port
                ):
                    # If backend has not changed, keep the same backend_client
                    new_backend_clients[backend_id] = self.backend_clients[backend_id]
                    continue

            # If the backend is new, or has changed, create a new backend_client
            backend_client = BackendClient(
                backend_info.host, backend_info.port, backend_id=backend_info.id
            )
            new_backend_clients[backend_info.id] = backend_client

        self.backend_clients = new_backend_clients

    def update_backend_clients(self):
        backend_infos = self.metadata_service.get_all_backends(from_backend=self.is_backend)
        logger.debug("Updating backend clients. Metadata reports #%d", len(backend_infos))
        new_backend_clients = {}

        # This only applies to the client, or at least, when client settings are set
        use_proxy = settings.client is not None and settings.client.proxy_enabled
        # (Backends will have settings.client = None by default)

        def add_backend_client(backend_info: Backend):
            if (
                backend_info.id in self.backend_clients
                and (
                    use_proxy
                    or (
                        backend_info.host == self.backend_clients[backend_info.id].host
                        and backend_info.port == self.backend_clients[backend_info.id].port
                    )
                )
                and self.backend_clients[backend_info.id].is_ready(settings.timeout_channel_ready)
            ):
                logger.debug("Existing backend already available: %s", backend_info.id)
                new_backend_clients[backend_info.id] = self.backend_clients[backend_info.id]
                return

            if use_proxy:
                logger.debug("New backend %s, connecting through proxy", backend_info.id)
                backend_client = BackendClient(
                    settings.client.proxy_host,
                    settings.client.proxy_port,
                    backend_id=backend_info.id,
                )
            else:
                logger.debug(
                    "New backend %s at %s:%s", backend_info.id, backend_info.host, backend_info.port
                )
                backend_client = BackendClient(
                    backend_info.host, backend_info.port, backend_id=backend_info.id
                )

            if backend_client.is_ready(settings.timeout_channel_ready):
                new_backend_clients[backend_info.id] = backend_client
            else:
                logger.info("Backend %s gave a timeout, removing it from list", backend_info.id)
                del backend_infos[backend_info.id]

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(add_backend_client, backend_info)
                for backend_info in backend_infos.values()
            ]
            concurrent.futures.wait(futures)
            # results = [future.result() for future in futures]

        logger.debug("Current list of backends: %s", new_backend_clients)
        self.backend_clients = new_backend_clients

    #################
    # Store Methods #
    #################

    def send_objects(
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

        visited_local_objects = {}
        pending_remote_objects = {}
        serialized_local_objects = []

        for instance in instances:
            # NOTE: We cannot make a replica of a replica because we need a global lock
            # of the metadata to keep consistency of _dc_meta.replica_backend_ids. Therefore,
            # we only allow to make replicas of master objects, which will acquire a lock
            # when updating the metadata.
            if instance._dc_is_local and not instance._dc_is_replica:
                if instance._dc_meta.id in visited_local_objects:
                    continue
                visited_local_objects[instance._dc_meta.id] = instance

                if not instance._dc_is_loaded:
                    self.data_manager.load_object(instance)
                if recursive:
                    if remotes:
                        serialized_objects = recursive_dcdumps(
                            instance, visited_local_objects, pending_remote_objects
                        )
                    else:
                        serialized_objects = recursive_dcdumps(instance, visited_local_objects)

                    serialized_local_objects.extend(serialized_objects)
                else:
                    object_bytes = dcdumps(instance._dc_state)
                    serialized_local_objects.append(object_bytes)
            else:
                pending_remote_objects[instance._dc_meta.id] = instance

        # Check that the destination backend is not this
        if backend_id != self.backend_id:
            backend_client = self.get_backend_client(backend_id)
            backend_client.register_objects(serialized_local_objects, make_replica=make_replica)

            for local_object in visited_local_objects.values():
                if make_replica:
                    local_object._dc_meta.replica_backend_ids.add(backend_id)
                else:
                    # Moving object
                    # TODO: Remove pickle file to reduce space
                    self.data_manager.remove_hard_reference(local_object)
                    local_object._clean_dc_properties()
                    local_object._dc_is_local = False
                    local_object._dc_is_loaded = False
                    local_object._dc_meta.master_backend_id = backend_id
                    local_object._dc_meta.replica_backend_ids.discard(backend_id)

        # Get the backend with most remote references.
        counter = collections.Counter()
        for remote_object in pending_remote_objects.values():
            counter[remote_object._dc_meta.master_backend_id] += 1
            if make_replica:
                if backend_id != remote_object._dc_meta.master_backend_id:
                    remote_object._dc_meta.replica_backend_ids.add(backend_id)
            else:
                remote_object._dc_meta.master_backend_id = backend_id
                remote_object._dc_meta.replica_backend_ids.discard(backend_id)

        assert counter[self.backend_id] == 0

        if len(counter) > 0:
            remote_backend_id = counter.most_common(1)[0][0]
            remote_backend_client = self.get_backend_client(remote_backend_id)
            remote_backend_client.send_objects(
                pending_remote_objects.keys(), backend_id, make_replica, recursive, remotes
            )

    def replace_object_properties(self, instance: DataClayObject, new_instance: DataClayObject):
        new_object_properties = self.get_object_properties(new_instance)
        self.update_object_properties(instance, new_object_properties)

    def update_object_properties(self, instance: DataClayObject, new_properties: dict[str, Any]):
        if instance._dc_is_local:
            vars(instance).update(new_properties)
            instance._dc_is_loaded = True
        else:
            backend_client = self.get_backend_client(instance._dc_meta.master_backend_id)
            backend_client.update_object_properties(instance._dc_meta.id, dcdumps(new_properties))

    def new_object_version(self, instance: DataClayObject, backend_id: Optional[UUID] = None):
        new_version = self.make_object_copy(instance, is_proxy=True)

        if instance._dc_meta.original_object_id is None:
            new_version._dc_meta.original_object_id = instance._dc_meta.id

        else:
            new_version._dc_meta.original_object_id = instance._dc_meta.original_object_id
            new_version._dc_meta.versions_object_ids = instance._dc_meta.versions_object_ids + [
                instance._dc_meta.id
            ]

        new_version._dc_meta.dataset_name = instance._dc_meta.dataset_name

        self.make_persistent(new_version, backend_id=backend_id)
        return new_version

    def consolidate_version(self, instance: DataClayObject):
        if instance._dc_meta.original_object_id is None:
            raise ObjectIsNotVersionError(instance._dc_meta.id)

        original_object_id = instance._dc_meta.original_object_id

        for version_object_id in instance._dc_meta.versions_object_ids:
            version = self.get_object_by_id(version_object_id)
            self.proxify_object(version, original_object_id)

        original_object = self.get_object_by_id(original_object_id)
        self.proxify_object(original_object, original_object_id)
        self.change_object_id(instance, original_object_id)

        instance._dc_meta.original_object_id = None
        instance._dc_meta.versions_object_ids = []

    ############
    # Replicas #
    ############

    def new_object_replica(
        self,
        instance: DataClayObject,
        backend_id: Optional[UUID] = None,
        recursive: bool = False,
        remotes: bool = True,
    ):
        logger.debug("Starting new replica of %s", instance._dc_meta.id)

        if not instance._dc_is_registered:
            raise ObjectNotRegisteredError(instance._dc_meta.id)

        if backend_id is None:
            # Get the backends that do not have a replica of the object
            avail_backends = set(self.backend_clients.keys()) - instance._dc_all_backend_ids

            # If there is no backend without a replica, update the list of backend clients,
            # sync the object metadata, and try again
            if not avail_backends:
                self.update_backend_clients()
                instance.sync()
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
            instance.sync()
            if backend_id in instance._dc_meta.replica_backend_ids:
                logger.warning("The backend already have a replica")
                # If not recursive, no need to continue
                if not recursive:
                    return

        self.send_objects([instance], backend_id, True, recursive, remotes)

    #####################
    # Garbage collector #
    #####################

    @abstractmethod
    def detach_object_from_session(self, object_id: UUID, hint):
        """Detach object from current session in use, i.e. remove reference from current session provided to object,

        'Dear garbage-collector, current session is not using the object anymore'
        """
        pass

    def add_session_reference(self, object_id: UUID):
        """reference associated to thread session

        Only implemented in BackendRuntime
        """
        pass

    ######################

    # TODO: Change name to something like get_other_backend...
    def prepare_for_new_replica_version_consolidate(
        self, object_id, hint, backend_id, backend_host, different_location
    ):
        """Helper function to prepare information for new replica - version - consolidate algorithms

        Args:
            object_id: id of the object
            backend_id: Destination backend ID to get information from (can be none)
            backend_host: Destination host to get information from (can be null)
            different_location:
                If true indicates that destination backend
                should be different to any location of the object
        Returns:
            Tuple with destination backend API to call and:
                Either information of dest backend with id provided,
                some exec env in host provided or random exec env.
        """

        raise Exception("Deprecated?¿")
        # NOTE ¿It should never happen?
        if hint is None:
            instance = self.inmemory_objects[object_id]
            self.sync_object_metadata(instance)
            hint = instance._dc_meta.master_backend_id

        dest_backend_id = backend_id
        dest_backend = None
        if dest_backend_id is None:
            if backend_host is not None:
                exec_envs_at_host = self.get_all_execution_environments_at_host(backend_host)
                if len(exec_envs_at_host) > 0:
                    dest_backend = list(exec_envs_at_host.values())[0]
                    dest_backend_id = dest_backend.id
            if dest_backend is None:
                if different_location:
                    # no destination specified, get one destination in which object is not already replicated
                    obj_locations = self.get_all_locations(object_id)
                    all_exec_envs = self.get_all_execution_environments_at_dataclay(
                        self.dataclay_id
                    )
                    for exec_env_id, exec_env in all_exec_envs.items():
                        logger.debug("Checking if %s is in %s", exec_env_id, obj_locations)
                        for obj_location in obj_locations:
                            if str(exec_env_id) != str(obj_location):
                                dest_backend_id = exec_env_id
                                dest_backend = exec_env
                                break
                    if dest_backend is None:
                        logger.debug(
                            "Could not find any different location for replica, updating available exec envs"
                        )
                        # retry updating locations
                        self.update_ee_infos()
                        all_exec_envs = self.get_all_execution_environments_at_dataclay(
                            self.dataclay_id
                        )
                        for exec_env_id, exec_env in all_exec_envs.items():
                            for obj_location in obj_locations:
                                if str(exec_env_id) != str(obj_location):
                                    dest_backend_id = exec_env_id
                                    dest_backend = exec_env
                                    break
                if dest_backend is None:
                    dest_backend_id = hint
                    dest_backend = self.get_execution_environment_info(dest_backend_id)

        else:
            dest_backend = self.get_execution_environment_info(dest_backend_id)

        try:
            ee_client = self.backend_clients[hint]
        except KeyError:
            backend_to_call = self.get_execution_environment_info(hint)
            ee_client = BackendClient(backend_to_call.host, backend_to_call.port)
            self.backend_clients[hint] = ee_client
        return ee_client, dest_backend

    ##############
    # Federation #
    ##############

    def federate_object(self, dc_obj, ext_dataclay_id, recursive):
        external_execution_environment_id = next(
            iter(self.get_all_execution_environments_at_dataclay(ext_dataclay_id))
        )
        self.federate_to_backend(dc_obj, external_execution_environment_id, recursive)

    @abstractmethod
    def federate_to_backend(self, dc_obj, external_execution_environment_id, recursive):
        pass

    def unfederate_object(self, dc_obj, ext_dataclay_id, recursive):
        self.unfederate_from_backend(dc_obj, None, recursive)

    @abstractmethod
    def unfederate_from_backend(self, dc_obj, external_execution_environment_id, recursive):
        pass

    def unfederate_all_objects(self, ext_dataclay_id):
        raise NotImplementedError()

    def unfederate_all_objects_with_all_dcs(self):
        raise NotImplementedError()

    def unfederate_object_with_all_dcs(self, dc_obj, recursive):
        raise NotImplementedError()

    def migrate_federated_objects(self, origin_dataclay_id, dest_dataclay_id):
        raise NotImplementedError()

    def federate_all_objects(self, dest_dataclay_id):
        raise NotImplementedError()

    def register_external_dataclay(self, id, host, port):
        """Register external dataClay for federation
        Args:
            host: external dataClay host name
            port: external dataClay port
        """
        self.metadata_service.autoregister_mds(id, host, port)

    ###########
    # Tracing #
    ###########

    def activate_tracing(self, initialize):
        """Activate tracing"""
        initialize_extrae(initialize)

    def deactivate_tracing(self, finalize_extrae):
        """Close the runtime paraver manager and deactivate the traces in LM (That deactivate also the DS)"""
        finish_tracing(finalize_extrae)

    def activate_tracing_in_dataclay_services(self):
        """Activate the traces in LM (That activate also the DS)"""
        if extrae_tracing_is_enabled():
            self.backend_clients["@LM"].activate_tracing(get_current_available_task_id())

    def deactivate_tracing_in_dataclay_services(self):
        """Deactivate the traces in LM and DSs"""
        if extrae_tracing_is_enabled():
            self.backend_clients["@LM"].deactivate_tracing()

    def get_traces_in_dataclay_services(self):
        """Get temporary traces from LM and DSs and store it in current workspace"""
        traces = self.backend_clients["@LM"].get_traces()
        traces_dir = settings.TRACES_DEST_PATH
        if len(traces) > 0:
            set_path = settings.TRACES_DEST_PATH + "/set-0"
            trace_mpits = settings.TRACES_DEST_PATH + "/TRACE.mpits"
            with open(trace_mpits, "a+") as trace_file:
                # store them here
                for key, value in traces.items():
                    dest_path = set_path + "/" + key
                    logger.debug("Storing object %s" % dest_path)
                    with open(dest_path, "wb") as dest_file:
                        dest_file.write(value)
                        dest_file.close()
                    if key.endswith("mpit"):
                        pointer = str(dest_path) + " named\n"
                        trace_file.write(pointer)
                        logger.debug("Appending to %s line: %s" % (trace_mpits, pointer))
                trace_file.flush()
                trace_file.close()

    ############
    # Shutdown #
    ############

    @abstractmethod
    def stop(self):
        pass

    def close_backend_clients(self):
        """Stop connections and daemon threads."""
        logger.debug("** Stopping runtime **")
        for name, client in self.backend_clients.items():
            logger.debug("Closing client connection to %s", name)
            client.close()
        self.backend_clients = {}

    ################## EXTRAE IGNORED FUNCTIONS ###########################
    deactivate_tracing.do_not_trace = True
    activate_tracing.do_not_trace = True
    activate_tracing_in_dataclay_services.do_not_trace = True
    deactivate_tracing_in_dataclay_services.do_not_trace = True
