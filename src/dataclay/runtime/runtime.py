""" Class description goes here. """
from __future__ import annotations

import copy
import importlib
import logging
import pickle
from abc import ABC, abstractmethod
from builtins import Exception
from typing import TYPE_CHECKING
from uuid import UUID
from weakref import WeakValueDictionary

from dataclay import utils
from dataclay.backend.client import BackendClient
from dataclay.conf import settings
from dataclay.dataclay_object import DataClayObject
from dataclay.exceptions import *
from dataclay.protos.common_messages_pb2 import LANG_PYTHON
from dataclay.runtime import UUIDLock
from dataclay.utils.telemetry import trace

if TYPE_CHECKING:
    from dataclay.dataclay_object import DataClayObject
    from dataclay.metadata.api import MetadataAPI
    from dataclay.metadata.client import MetadataClient
    from dataclay.metadata.kvdata import ObjectMetadata

tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)


class DataClayRuntime(ABC):
    def __init__(self, metadata_service: MetadataAPI | MetadataClient):
        self.backend_clients: dict[UUID, BackendClient] = dict()
        self._dataclay_id = None
        self.metadata_service = metadata_service

        # Memory objects. This dictionary must contain all objects in runtime memory (client or server), as weakrefs.
        self.inmemory_objects = WeakValueDictionary()
        utils.metrics.dataclay_inmemory_objects.set_function(lambda: len(self.inmemory_objects))

    ##############
    # Properties #
    ##############

    @property
    @abstractmethod
    def session(self):
        pass

    @property
    @abstractmethod
    def is_backend(self):
        pass

    # Common runtime API

    @abstractmethod
    def make_persistent(self, instance, alias, backend_id):
        pass

    @abstractmethod
    def add_to_heap(self, instance: DataClayObject):
        pass

    def load_object_from_db(self, instance: DataClayObject):
        pass

    ##############
    # Get Object #
    ##############

    # TODO: Check if is taking the metrics from KeyError, if not put inside
    @utils.metrics.dataclay_inmemory_misses_total.count_exceptions(KeyError)
    def get_object_by_id(self, object_id: UUID, object_md: ObjectMetadata = None) -> DataClayObject:
        """Get dataclay object from inmemory_objects. If not present, get object metadata
        and create new proxy object.
        """
        logger.debug(f"Get object {object_id} by id")

        # Check if object is in heap
        try:
            dc_object = self.inmemory_objects[object_id]
            utils.metrics.dataclay_inmemory_hits_total.inc()
            return dc_object
        except KeyError:
            with UUIDLock(object_id):
                try:
                    dc_object = self.inmemory_objects[object_id]
                    utils.metrics.dataclay_inmemory_hits_total.inc()
                    return dc_object
                except KeyError:
                    # NOTE: When the object is not in the inmemory_objects,
                    # we get the object metadata from etcd, and create a new proxy
                    # object from it.

                    if object_md is None:
                        object_md = self.metadata_service.get_object_md_by_id(object_id)

                    cls = utils.get_class_by_name(object_md.class_name)

                    proxy_object = cls.new_proxy_object()
                    proxy_object.metadata = object_md

                    if (
                        self.is_backend
                        and proxy_object._dc_backend_id == settings.DATACLAY_BACKEND_ID
                    ):
                        proxy_object._dc_is_local = True
                    else:
                        proxy_object._dc_is_local = False

                    proxy_object._dc_is_loaded = False
                    proxy_object._dc_is_registered = True

                    # Since it is no loaded, we only add it to the inmemory list
                    # The object will be loaded if needed calling "load_object_from_db"
                    self.inmemory_objects[proxy_object._dc_id] = proxy_object
                    return proxy_object

    def get_object_by_alias(self, alias, dataset_name=None) -> DataClayObject:
        """Get object instance from alias"""

        if dataset_name is None:
            dataset_name = self.session.dataset_name

        object_md = self.metadata_service.get_object_md_by_alias(alias, dataset_name)

        return self.get_object_by_id(object_md.id, object_md)

    ##################
    # Active Methods #
    ##################

    def call_active_method(self, instance, method_name, args: tuple, kwargs: dict):
        with tracer.start_as_current_span("call_active_method") as span:
            span.set_attribute("class", str(instance._dc_class_name))
            span.set_attribute("method", str(method_name))
            span.set_attribute("args", str(args))
            span.set_attribute("kwargs", str(kwargs))

            serialized_args = pickle.dumps(args)
            serialized_kwargs = pickle.dumps(kwargs)
            # TODO: Add serialized volatile objects to
            # self.volatile_parameters_being_send to avoid race conditon.
            # May be necessary a custom pickle.Pickler
            # TODO: Check if race conditions can happend (chek old call_execute_to_ds)

            # NOTE: Loop to update the backend_id when we have the wrong one, and call again
            # the active method
            while True:
                backend_client = self.get_backend_client(instance._dc_backend_id)

                serialized_response, is_exception = backend_client.call_active_method(
                    self.session.id,
                    instance._dc_id,
                    method_name,
                    serialized_args,
                    serialized_kwargs,
                )

                if serialized_response:
                    response = pickle.loads(serialized_response)

                    if isinstance(response, ObjectWithWrongBackendId):
                        instance._dc_backend_id = response.backend_id
                        continue

                    if is_exception:
                        raise response

                    return response

                else:
                    return None

    #########
    # Alias #
    #########

    def add_alias(self, instance, alias):
        self.metadata_service.new_alias(alias, instance._dc_dataset_name, instance._dc_id)

    def delete_alias(self, alias, dataset_name):
        if dataset_name is None:
            dataset_name = self.session.dataset_name

        self.metadata_service.delete_alias(alias, dataset_name, self.session.id)

    def update_object_metadata(self, instance: DataClayObject):
        object_md = self.metadata_service.get_object_md_by_id(instance._dc_id)
        instance.metadata = object_md

    def get_all_alias(self, dataset_name: str = None, object_id: UUID = None):
        return self.metadata_service.get_all_alias(dataset_name, object_id)

    ############
    # Backends #
    ############

    def get_backend_client(self, backend_id: UUID) -> BackendClient:
        try:
            return self.backend_clients[backend_id]
        except KeyError:
            self.update_backend_clients()
            return self.backend_clients[backend_id]

    def update_backend_clients(self):
        backend_infos = self.metadata_service.get_all_backends(from_backend=self.is_backend)
        new_backend_clients = {}

        # TODO: Update backend_clients using multithreading
        for id, info in backend_infos.items():
            if id in self.backend_clients:
                if self.backend_clients[id].is_ready(settings.TIMEOUT_CHANNEL_READY):
                    new_backend_clients[id] = self.backend_clients[id]
                    continue

            backend_client = BackendClient(info.hostname, info.port)
            if backend_client.is_ready(settings.TIMEOUT_CHANNEL_READY):
                new_backend_clients[id] = backend_client
            else:
                del backend_infos[id]

        self.backend_clients = new_backend_clients

    #################
    # Store Methods #
    #################

    def get_object_properties(self, instance):
        if instance._dc_is_local:
            self.load_object_from_db(instance)
            return instance._dc_properties
        else:
            backend_client = self.get_backend_client(instance._dc_backend_id)
            serialized_properties = backend_client.get_object_properties(instance._dc_id)
            return pickle.loads(serialized_properties)

    def make_object_copy(self, instance, recursive=None):
        # It cannot be called if instnace is not persistent, because
        # the deepcopy from the class will try to serialize the instance
        # and it will be made persistent in the process
        # A solution could be to override the __deepcopy__, but I don't see the need...
        object_properties = copy.deepcopy(self.get_object_properties(instance))
        # object_copy = instance.__class__.__new__(__class__)
        object_copy = DataClayObject.__new__(instance.__class__)
        vars(object_copy).update(object_properties)
        return object_copy

    def replace_object_properties(self, instance, new_instance):
        new_object_properties = self.get_object_properties(new_instance)
        self.update_object_properties(instance, new_object_properties)

    def update_object_properties(self, instance, new_properties):
        if instance._dc_is_local:
            self.load_object_from_db(instance)
            vars(instance).update(new_properties)
        else:
            backend_client = self.get_backend_client(instance._dc_backend_id)
            backend_client.update_object_properties(instance._dc_id, pickle.dumps(new_properties))

    def make_new_version(self, instance, backend_id=None):
        new_version = self.make_object_copy(instance)

        if instance._dc_original_object_id is None:
            new_version._dc_original_object_id = instance._dc_id

        else:
            new_version._dc_original_object_id = instance._dc_original_object_id
            new_version._dc_versions_object_ids = instance._dc_versions_object_ids + [
                instance._dc_id
            ]

        new_version._dc_dataset_name = instance._dc_dataset_name

        if not new_version._dc_is_registered:
            self.make_persistent(new_version, backend_id=backend_id)

        return new_version

    def consolidate_version(self, instance):
        if instance._dc_original_object_id is None:
            logger.warning("Trying to consolidate an object that is not a version")
            return

        original_object_id = instance._dc_original_object_id

        for version_object_id in instance._dc_versions_object_ids:
            version = self.get_object_by_id(version_object_id)
            self.proxify_object(version, original_object_id)

        original_object = self.get_object_by_id(original_object_id)
        self.proxify_object(original_object, original_object_id)
        self.change_object_id(instance, original_object_id)

        instance._dc_original_object_id = None
        instance._dc_versions_object_ids = []

    def proxify_object(self, instance, new_object_id):
        if instance._dc_is_local:
            with UUIDLock(instance._dc_id):
                self.load_object_from_db(instance)
                instance._clean_dc_properties()
                instance._dc_is_loaded = False
                instance._dc_is_local = False
                self.heap_manager.release_from_heap(instance)
                # NOTE: There is no need to delete, and it may be good
                # in case that an object was serialized to disk before a
                # consolidation. However, it will be deleted also since
                # inmemory_objects is a weakref dict.
                # del self.inmemory_objects[instance._dc_id]
                self.metadata_service.delete_object(instance._dc_id)
        else:
            backend_client = self.get_backend_client(instance._dc_backend_id)
            backend_client.proxify_object(instance._dc_id, new_object_id)

        instance._dc_id = new_object_id

    def change_object_id(self, instance, new_object_id):
        old_object_id = instance._dc_id

        if instance._dc_is_local:
            with UUIDLock(instance._dc_id):
                self.load_object_from_db(instance)
                # We need to update the loaded_objects with the new object_id key
                self.heap_manager.release_from_heap(instance)
                instance._dc_id = new_object_id
                self.heap_manager.retain_in_heap(instance)
                # Also update the inmemory_objects with the new object_id key
                self.inmemory_objects[new_object_id] = instance
                self.metadata_service.change_object_id(old_object_id, new_object_id)

                # The only use case for change_object_id is to consolidate, therefore:
                instance._dc_original_object_id = None
                instance._dc_versions_object_ids = []
                self.metadata_service.register_object(instance.metadata)
        else:
            backend_client = self.get_backend_client(instance._dc_backend_id)
            backend_client.change_object_id(instance._dc_id, new_object_id)
            instance._dc_id = new_object_id

        del self.inmemory_objects[old_object_id]

    #####################
    # Garbage collector #
    #####################

    @abstractmethod
    def detach_object_from_session(self, object_id, hint):
        """Detach object from current session in use, i.e. remove reference from current session provided to object,

        'Dear garbage-collector, current session is not using the object anymore'
        """
        pass

    def add_session_reference(self, object_id):
        """reference associated to thread session

        Only implemented in BackendRuntime
        """
        pass

    ############
    # Replicas #
    ############

    # TODO: Change name to something like get_other_backend...
    def prepare_for_new_replica_version_consolidate(
        self, object_id, hint, backend_id, backend_hostname, different_location
    ):
        """Helper function to prepare information for new replica - version - consolidate algorithms

        Args:
            object_id: id of the object
            backend_id: Destination backend ID to get information from (can be none)
            backend_hostname: Destination hostname to get information from (can be null)
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
            self.update_object_metadata(instance)
            hint = instance._dc_backend_id

        dest_backend_id = backend_id
        dest_backend = None
        if dest_backend_id is None:
            if backend_hostname is not None:
                exec_envs_at_host = self.get_all_execution_environments_at_host(backend_hostname)
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
                        logger.debug(f"Checking if {exec_env_id} is in {obj_locations}")
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
            ee_client = BackendClient(backend_to_call.hostname, backend_to_call.port)
            self.backend_clients[hint] = ee_client
        return ee_client, dest_backend

    def new_replica(self, object_id, hint, backend_id, backend_hostname, recursive):
        logger.debug(f"Starting new replica of {object_id}")
        # IMPORTANT NOTE: pyclay is not able to replicate/versionate/consolidate Java or other language objects

        ee_client, dest_backend = self.prepare_for_new_replica_version_consolidate(
            object_id, hint, backend_id, backend_hostname, True
        )
        replicated_object_ids = ee_client.new_replica(
            self.session.id, object_id, dest_backend.id, recursive
        )
        logger.debug(f"Replicated: {replicated_object_ids} into {dest_backend.id}")
        # Update replicated objects metadata
        for replicated_object_id in replicated_object_ids:
            # NOTE: If it fails, use object_id instead of replicated_object_id
            instance = self.inmemory_objects[replicated_object_id]
            instance._add_replica_location(dest_backend.id)
            if instance.get_origin_location() is None:
                # NOTE: at client side there cannot be two replicas of same oid
                instance.set_origin_location(hint)
        return dest_backend.id

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

    def register_external_dataclay(self, id, hostname, port):
        """Register external dataClay for federation
        Args:
            hostname: external dataClay host name
            port: external dataClay port
        """
        self.metadata_service.autoregister_mds(id, hostname, port)

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

    def stop_gc(self):
        """Stop GC. useful for shutdown."""
        # Stop HeapManager
        logger.debug("Stopping GC. Sending shutdown event.")
        self.heap_manager.shutdown()
        logger.debug("Waiting for GC.")
        self.heap_manager.join()
        logger.debug("GC stopped.")

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