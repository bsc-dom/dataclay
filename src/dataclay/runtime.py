""" Class description goes here. """
from __future__ import annotations

import importlib
import logging
import uuid
from abc import ABC, abstractmethod
from builtins import Exception
from contextlib import AbstractContextManager
from threading import Condition
from typing import TYPE_CHECKING
from uuid import UUID
from weakref import WeakValueDictionary

import grpc

from dataclay.backend.client import BackendClient
from dataclay.conf import settings
from dataclay.protos.common_messages_pb2 import LANG_PYTHON

if TYPE_CHECKING:

    from dataclay.dataclay_object import DataClayObject
    from dataclay.metadata.api import MetadataAPI
    from dataclay.metadata.client import MetadataClient
    from dataclay.metadata.managers.dataclay import Backend
    from dataclay.metadata.managers.object import ObjectMetadata


logger = logging.getLogger(__name__)


current_runtime = None


def get_runtime() -> DataClayRuntime:
    return current_runtime


def set_runtime(new_runtime):
    global current_runtime
    current_runtime = new_runtime


class UUIDLock(AbstractContextManager):
    """This class is used as a global lock for UUIDs

    Use it always with context manager:
        with UUIDLock(id):
            ...
    """

    cv = Condition()
    locked_objects = set()

    def __init__(self, id):
        self.id = id

    def __enter__(self):
        with self.cv:
            self.cv.wait_for(lambda: self.id not in self.locked_objects)
            self.locked_objects.add(self.id)

    def __exit__(self, exc_type, exc_value, traceback):
        with self.cv:
            self.locked_objects.remove(self.id)
            self.cv.notify_all()


class DataClayRuntime(ABC):
    def __init__(self, metadata_service: MetadataAPI | MetadataClient):

        self.backend_clients: dict[UUID, BackendClient] = dict()

        # Indicates volatiles being send - to avoid race-conditions
        self.volatile_parameters_being_send = set()

        # Current dataClay ID
        self._dataclay_id = None

        # volatiles currently under deserialization
        self.volatiles_under_deserialization = dict()

        self.metadata_service = metadata_service

        # Memory objects. This dictionary must contain all objects in runtime memory (client or server), as weakrefs.
        self.inmemory_objects = WeakValueDictionary()

    ##############
    # Properties #
    ##############

    @property
    @abstractmethod
    def session(self):
        pass

    @property
    def dataclay_id(self):
        """Get dataClay UUID of current dataClay"""
        if self._dataclay_id is None:
            self._dataclay_id = self.metadata_service.get_dataclay_id()
        return self._dataclay_id

    @property
    @abstractmethod
    def is_backend(self):
        pass

    ##
    # Common runtime API
    ##

    @abstractmethod
    def make_persistent(self, instance, alias, backend_id, recursive):
        pass

    @abstractmethod
    def add_to_heap(self, instance: DataClayObject):
        pass

    ########
    # Heap #
    ########

    def exists(self, object_id):
        return object_id in self.inmemory_objects

    def heap_size(self):
        return len(self.inmemory_objects)

    #############
    # Volatiles #
    #############

    def add_volatiles_under_deserialization(self, volatiles):
        """Add volatiles provided to be 'under deserialization' in case any execution
        in a volatile is thrown before it is completely deserialized.

        This is needed in case any deserialization depends on another (not for race conditions)
        like hashcodes or other similar cases.

        Args:
            volatiles: volatiles under deserialization
        """
        for vol_obj in volatiles:
            self.volatiles_under_deserialization[vol_obj.object_id] = vol_obj

    def remove_volatiles_under_deserialization(self, volatiles):
        """Remove volatiles under deserialization"""
        for vol_obj in volatiles:
            if vol_obj.object_id in self.volatiles_under_deserialization:
                del self.volatiles_under_deserialization[vol_obj.object_id]

    def update_object(self, into_object, from_object):
        session_id = self.session.id

        backend_id = into_object._dc_backend_id
        ee_client = self.get_backend_client(backend_id)

        # We serialize objects like volatile parameters
        parameters = list()
        parameters.append(from_object)
        # TODO: modify serialize_params_or_return to not require this
        params_order = list()
        params_order.append("object")
        params_spec = dict()
        params_spec["object"] = "DataClayObject"  # not used, see serialized_params_or_return
        serialized_params = SerializationLibUtilsSingleton.serialize_params_or_return(
            params=parameters,
            iface_bitmaps=None,
            params_spec=params_spec,
            params_order=params_order,
            hint_volatiles=backend_id,
            runtime=self,
            recursive=True,
            for_update=True,
        )

        vol_objects = serialized_params.vol_objs
        if vol_objects is not None:
            new_ids = dict()

            for tag in vol_objects:
                cur_oid = serialized_params.vol_objs[tag].object_id
                if cur_oid not in new_ids:
                    if cur_oid == from_object._dc_id:
                        new_ids[cur_oid] = into_object._dc_id
                    else:
                        new_ids[cur_oid] = uuid.uuid4()

                serialized_params.vol_objs[tag] = ObjectWithDataParamOrReturn(
                    new_ids[cur_oid],
                    serialized_params.vol_objs[tag].class_id,
                    serialized_params.vol_objs[tag].metadata,
                    serialized_params.vol_objs[tag].obj_bytes,
                )

            for vol_tag in vol_objects:
                oids = serialized_params.vol_objs[vol_tag].metadata.tags_to_oids
                for tag, oid in oids.items():
                    if oid in new_ids:
                        try:
                            serialized_params.vol_objs[vol_tag].metadata.tags_to_oids[
                                tag
                            ] = new_ids[oid]
                        except KeyError:
                            pass

        ee_client.ds_update_object(session_id, into_object._dc_id, serialized_params)

    ###################
    # Object Metadata #
    ###################

    def get_object_by_id(self, object_id: UUID, object_md: ObjectMetadata = None) -> DataClayObject:
        """Get dataclay object from inmemory_objects. If not present, get object metadata
        and create new proxy object.
        """
        logger.debug(f"Get object {object_id} by id")

        # Check if object is in heap
        try:
            return self.inmemory_objects[object_id]
        except KeyError:
            with UUIDLock(object_id):
                try:
                    return self.inmemory_objects[object_id]
                except KeyError:

                    # NOTE: When the object is not in the inmemory_objects,
                    # we get the object metadata from etcd, and create a new proxy
                    # object from it.

                    if object_md is None:
                        object_md = self.metadata_service.get_object_md_by_id(object_id)

                    module_name, class_name = object_md.class_name.rsplit(".", 1)
                    m = importlib.import_module(module_name)
                    cls = getattr(m, class_name)

                    proxy_object = cls.new_proxy_object()
                    proxy_object.metadata = object_md

                    if self.is_backend and proxy_object._dc_backend_id == settings.DC_BACKEND_ID:
                        proxy_object._dc_is_local = True
                    else:
                        proxy_object._dc_is_local = False

                    proxy_object._dc_is_loaded = False
                    proxy_object._dc_is_registered = True

                    # Since it is no loaded, we only add it to the inmemory list
                    self.inmemory_objects[proxy_object._dc_id] = proxy_object
                    return proxy_object

    def get_object_by_alias(self, alias, dataset_name=None) -> DataClayObject:
        """Get object instance from alias"""

        if dataset_name is None:
            dataset_name = self.session.dataset_name

        object_md = self.metadata_service.get_object_md_by_alias(alias, dataset_name)

        return self.get_object_by_id(object_md.id, object_md)

    def delete_alias_in_dataclay(self, alias, dataset_name):

        if dataset_name is None:
            dataset_name = self.session.dataset_name

        self.metadata_service.delete_alias(alias, dataset_name, self.session.id)

    @abstractmethod
    def delete_alias(self, dc_obj):
        pass

    # TODO: Check if can be deprecated and use get_all_backends
    def get_all_locations(self, object_id):
        locations = set()
        try:
            instance = self.inmemory_objects[object_id]
            locations.add(instance._dc_backend_id)
            locations.update(instance._dc_replica_backend_ids)
        except KeyError:
            object_md = self.metadata_service.get_object_md_by_id(object_id)
            locations.add(object_md.backend_id)
            locations.update(object_md.replica_backend_ids)
        return locations

    def update_object_metadata(self, instance: DataClayObject):
        object_md = self.metadata_service.get_object_md_by_id(instance._dc_id)
        instance.metadata = object_md

    #####################
    # Dataclay Metadata #
    #####################

    def get_num_objects(self):
        return self.metadata_service.get_num_objects(LANG_PYTHON)

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

    ##########################
    # Execution Environments #
    ##########################

    def get_backend_client(self, backend_id: UUID) -> BackendClient:
        try:
            return self.backend_clients[backend_id]
        except KeyError:
            self.update_backend_clients()
            return self.backend_clients[backend_id]

    def update_backend_clients(self):
        backend_infos = self.metadata_service.get_all_execution_environments(
            LANG_PYTHON, from_backend=self.is_backend
        )
        new_backend_clients = {}

        # TODO: Update backend_clients using multithreading
        for id, info in backend_infos.items():
            if id in self.backend_clients:
                if self.backend_clients[id].is_ready(settings.TIMEOUT_CHANNEL_READY):
                    new_backend_clients[id] = self.backend_clients[id]
                    continue

            backend_client = BackendClient(info.hostname, info.port)
            if backend_client.is_ready():
                new_backend_clients[id] = backend_client
            else:
                del backend_infos[id]

        self.backend_clients = new_backend_clients

    ####################
    # Remote execution #
    ####################

    def call_active_method(self, instance, method_name, args: tuple, kwargs: dict):
        import pickle

        serialized_args = pickle.dumps(args)
        serialized_kwargs = pickle.dumps(kwargs)
        # TODO: Add serialized volatile objects to
        # self.volatile_parameters_being_send to avoid race conditon.
        # May be necessary a custom pickle.Pickler

        backend_client = self.get_backend_client(instance._dc_backend_id)

        serialized_response = backend_client.call_active_method(
            self.session.id, instance._dc_id, method_name, serialized_args, serialized_kwargs
        )
        if serialized_response:
            response = pickle.loads(serialized_response)
            return response

    # DEPRECATED: Use call_active_method
    def call_execute_to_ds(self, instance, parameters, operation_name, exec_env_id, using_hint):
        raise Exception("Deprecated")
        object_id = instance._dc_id
        operation = self.get_operation_info(object_id, operation_name)
        session_id = self.session.id
        implementation_id = self.get_implementation_id(object_id, operation_name)

        print("----", locals())
        print("----", dir())

        # // === SERIALIZE PARAMETERS === //
        serialized_params = SerializationLibUtilsSingleton.serialize_params_or_return(
            params=parameters,
            iface_bitmaps=None,
            params_spec=operation.params,
            params_order=operation.paramsOrder,
            hint_volatiles=exec_env_id,
            runtime=self,
        )

        if serialized_params is not None and serialized_params.vol_objs is not None:
            for param in serialized_params.vol_objs.values():
                self.volatile_parameters_being_send.add(param.object_id)

        # // === EXECUTE === //
        max_retry = settings.MAX_EXECUTION_RETRIES
        num_misses = 0
        executed = False
        for _ in range(max_retry):

            ee_client = self.get_backend_client(backend_id)

            try:
                logger.debug("Calling remote EE %s ", exec_env_id)
                ret = ee_client.ds_execute_implementation(
                    object_id, implementation_id, session_id, serialized_params
                )
                executed = True
                break

            except (DataClayException, grpc.RpcError) as dce:
                logger.warning("Execution resulted in an error, retrying...", exc_info=dce)

                is_race_condition = False
                if serialized_params is not None and serialized_params.persistent_refs is not None:
                    for param in serialized_params.persistent_refs:
                        if param.object_id in self.volatile_parameters_being_send:
                            is_race_condition = True
                            break
                if not is_race_condition:
                    num_misses = num_misses + 1
                    logger.debug("Exception dataclay during execution. Retrying...")
                    logger.debug(str(dce))

                    locations = instance._dc_replica_backend_ids
                    if locations is None or len(locations) == 0:
                        try:
                            self.update_object_metadata(instance)
                            locations = instance._dc_replica_backend_ids
                            new_location = False
                        except DataClayException:
                            locations = None

                    if locations is None:
                        logger.warning(
                            "Execution failed and no metadata available. Cannot continue"
                        )
                        raise

                    for loc in locations:
                        logger.debug("Found location %s" % str(loc))
                        if loc != exec_env_id:
                            exec_env_id = loc
                            logger.debug("Found different location %s" % str(loc))
                            new_location = True
                            break

                    if not new_location:
                        exec_env_id = next(iter(locations))
                    if using_hint:
                        instance._dc_backend_id = exec_env_id
                    logger.debug(
                        "[==Miss Jump==] MISS. The object %s was not in the exec.location %s. Retrying execution."
                        % (instance._dc_id, str(exec_env_id))
                    )

        if serialized_params is not None and serialized_params.vol_objs is not None:
            for param in serialized_params.vol_objs.values():
                if num_misses > 0:
                    # ===========================================================
                    # if there was a miss, it means that the persistent object in which we were executing
                    # was not in the choosen location. As you can see in the serialize parameters function above
                    # we provide the execution environment as hint to set to volatile parameters. In EE, before
                    # deserialization of volatiles we check if the persistent object in which to execute a method is
                    # there, if not, EE raises and exception. Therefore, if there was a miss, we know that the
                    # hint we set in volatile parameters is wrong, because they are going to be deserialized/stored
                    # in the same location as the object with the method to execute
                    # ===========================================================
                    param_instance = self.inmemory_objects[param.object_id]
                    param_instance._dc_backend_id = exec_env_id
                self.volatile_parameters_being_send.remove(param.object_id)

        if not executed:
            raise RuntimeError(
                "[dataClay] ERROR: Trying to execute remotely object  but something went wrong. "
                "Maybe the object is still not stored (in case of asynchronous makepersistent) and "
                "waiting time is not enough. Maybe the object does not exist anymore due to a remove. "
                "Or Maybe an exception happened in the server and the call failed."
            )

        result = None
        if ret is None:
            logger.debug(f"Result of operation named {operation_name} received: None")
        else:
            logger.debug(
                f"Deserializing result of operation named {operation_name}, return type is {operation.returnType.signature}"
            )
            result = DeserializationLibUtilsSingleton.deserialize_return(
                ret, None, operation.returnType, self
            )
            logger.debug(
                f"Deserialization of result of operation named {operation_name} successfully finished."
            )
        return result

    #####################
    # Clone and replica #
    #####################

    def get_copy_of_object(self, from_object, recursive):
        session_id = self.session.id

        backend_id = from_object._dc_backend_id

        ee_client = self.get_backend_client(backend_id)

        copiedObject = ee_client.ds_get_copy_of_object(session_id, from_object._dc_id, recursive)
        result = DeserializationLibUtilsSingleton.deserialize_params_or_return(
            copiedObject, None, None, None, self
        )

        return result[0]

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
            instance.add_replica_location(dest_backend.id)
            if instance.get_origin_location() is None:
                # NOTE: at client side there cannot be two replicas of same oid
                instance.set_origin_location(hint)
        return dest_backend.id

    # NOTE: Used for compss
    def new_version(
        self, object_id, hint, class_id, dataset_name, backend_id, backend_hostname, recursive
    ):
        # IMPORTANT NOTE: pyclay is not able to replicate/versionate/consolidate Java or other language objects
        logger.debug(f"Starting new version of {object_id}")
        ee_client, dest_backend = self.prepare_for_new_replica_version_consolidate(
            object_id, hint, backend_id, backend_hostname, False
        )
        version_id = ee_client.new_version(self.session.id, object_id, dest_backend.id)
        logger.debug(f"Finished new version of {object_id}, created version {version_id}")
        return version_id, dest_backend.id

    def consolidate_version(self, object_id, hint):
        # IMPORTANT NOTE: pyclay is not able to replicate/versionate/consolidate Java or other language objects
        logger.debug(f"Starting consolidate version of {object_id}")

        # NOTE: ¿Can it happen?
        if hint is None:
            instance = self.inmemory_objects[object_id]
            self.update_object_metadata(instance)
            hint = self.get_hint(object_id)

        ee_client = self.get_backend_client(hint)
        ee_client.consolidate_version(self.session.id, object_id)
        logger.debug(f"Finished consolidate version of {object_id}")

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

    def import_models_from_external_dataclay(self, namespace, ext_dataclay_id) -> None:
        """Import models in namespace specified from an external dataClay
        :param namespace: external dataClay namespace to get
        :param ext_dataclay_id: external dataClay ID
        :return: None
        :type namespace: string
        :type ext_dataclay_id: UUID
        :rtype: None
        """
        logger.debug(
            f"[==Import_models_from_external_dataclay==] Registering namespace {namespace} from {ext_dataclay_id}"
        )
        self.backend_clients["@LM"].import_models_from_external_dataclay(namespace, ext_dataclay_id)

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
