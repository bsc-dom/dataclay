""" Class description goes here. """
import importlib
import logging
import os
import traceback
import uuid
from abc import ABCMeta, abstractmethod
from enum import Enum
from logging import TRACE

import six
from dataclay.communication.grpc.clients.ExecutionEnvGrpcClient import EEClient
from dataclay.communication.grpc.clients.LogicModuleGrpcClient import LMClient
from dataclay.exceptions.exceptions import DataClayException
from dataclay.heap.LockerPool import LockerPool
from dataclay.paraver import (
    extrae_tracing_is_enabled,
    finish_tracing,
    get_current_available_task_id,
    get_task_id,
    initialize_extrae,
)
from dataclay.serialization.lib.DeserializationLibUtils import DeserializationLibUtilsSingleton
from dataclay.serialization.lib.ObjectWithDataParamOrReturn import ObjectWithDataParamOrReturn
from dataclay.serialization.lib.SerializationLibUtils import SerializationLibUtilsSingleton
from dataclay.util import Configuration
from dataclay.util.management.metadataservice.MetaDataInfo import MetaDataInfo
from dataclay.util.management.metadataservice.RegistrationInfo import RegistrationInfo
from dataclay_common.protos.common_messages_pb2 import LANG_PYTHON
from grpc import RpcError
from lru import LRU


class NULL_NAMESPACE:
    """null Namespace for uuid3, same as java's UUID.nameUUIDFromBytes"""

    bytes = b""


@six.add_metaclass(ABCMeta)
class DataClayRuntime(object):

    """Logger"""

    logger = logging.getLogger("dataclay.api")

    def __init__(self):

        """Cache of EE info"""
        self.ee_info_map = None

        """ GRPC clients """
        self.ready_clients = dict()

        """ Cache of classes. TODO: is it used? -> Yes, in StubUtils and ClientObjectLoader"""
        self.local_available_classes = dict()

        """  Heap manager. Since it is abstract it must be initialized by sub-classes. 
        DataClay-Java uses abstract functions to get the field in the proper type (EE or client) 
        due to type-check. Not needed here. """
        self.dataclay_heap_manager = None

        """ Object loader. """
        self.dataclay_object_loader = None

        """  Locker Pool in runtime. This pool is used to provide thread-safe implementations in dataClay. """
        self.locker_pool = LockerPool()

        """ Indicates if runtime was initialized. TODO: check if same in dataclay.api -> NO """
        self.__initialized = False

        """ Indicates volatiles being send - to avoid race-conditions """
        self.volatile_parameters_being_send = set()

        """ Cache of metadata """
        self.metadata_cache = LRU(10000)

        """ Current dataClay ID """
        self.dataclay_id = None

        """ volatiles currently under deserialization """
        self.volatiles_under_deserialization = dict()

    @abstractmethod
    def initialize_runtime_aux(self):
        pass

    def initialize_runtime(self):
        """
        IMPORTANT: get_runtime can be called from decorators, during imports, and therefore a runtime might be created.
        In that case we do NOT want to create threads to start. Only if "init" was called (client side) or
        server was started. This function is for that.
        """
        self.logger.debug("INITIALIZING RUNTIME")
        self.initialize_runtime_aux()
        self.dataclay_heap_manager.start()

    def is_initialized(self):
        """
        @return: TRUE if runtime is initialized (Client 'init', EE should be always TRUE). False otherwise.
        """
        return self.__initialized

    def is_exec_env(self):
        # ExecutionEnvironmentRuntime must override to True.
        return False

    def is_client(self):
        # ClientRuntime must override to True
        return False

    @abstractmethod
    def get_session(self):
        pass

    @abstractmethod
    def detach_object_from_session(self, object_id, hint):
        """Detach object from current session in use, i.e. remove reference from current session provided to object,
        "dear garbage-collector, current session is not using the object anymore"
        :param object_id: id of the object
        :param hint: hint of the object
        :type object_id: uuid
        :type hint: uuid
        """
        pass

    def get_lm_api(self, host, port):
        """Get logic module connection.
        :param host: logic module host
        :param port: logic module port
        :type host: str
        :type port: str
        :returns: logic module api to connect
        :rtype: logic module grpc api
        """
        try:
            lm_client = self.ready_clients[host + ":" + str(port)]
        except KeyError:
            lm_client = LMClient(host, port)
            try:
                lm_client.check_alive()
            except:
                raise
            self.ready_clients[host + ":" + str(port)] = lm_client
        return lm_client

    @abstractmethod
    def get_operation_info(self, object_id, operation_name):
        pass

    @abstractmethod
    def get_implementation_id(self, object_id, operation_name, implementation_idx=0):
        pass

    def get_object_by_id(self, object_id, class_id=None, hint=None):
        """Get object instance directly from an object id, use class id and hint in
        case it is still not registered.
        :param object_id: id of the object to get
        :param class_id: class id of the object to get
        :param hint: hint of the object to get
        :returns: object instance
        :rtype: DataClayObject
        :type object_id: uuid
        :type class_id: uuid
        :type hint: uuid
        :rtype: DataClayObject
        """
        self.logger.debug(f"Get object {object_id} by id")
        o = self.get_from_heap(object_id)
        if o is not None:
            return o

        if not class_id:
            full_name, namespace = self.ready_clients["@LM"].get_object_info(
                self.get_session().id, object_id
            )
            self.logger.debug(
                "Trying to import full_name: %s from namespace %s", full_name, namespace
            )

            # Rearrange the division, full_name may include dots (and be nested)
            prefix, class_name = ("%s.%s" % (namespace, full_name)).rsplit(".", 1)
            m = importlib.import_module(prefix)
            klass = getattr(m, class_name)
            class_id = klass.get_class_extradata().class_id

        o = self.get_or_new_persistent_instance(object_id, class_id, hint)
        return o

    def add_to_heap(self, dc_object):
        """
        @postcondition: the object is added to dataClay's heap
        @param dc_object: object to add to the heap
        """
        self.dataclay_heap_manager.add_to_heap(dc_object)

    def update_object_id(self, dco, new_object_id):
        """Update the object id in both DataClayObject and HeapManager
        :param dco: a DataClay object.
        :param new_object_id: the new object id.
        :type dco: DataClayObject
        :type new_object_id: ObjectID
        """
        old_object_id = dco.get_object_id()
        dco.set_object_id(new_object_id)
        self.dataclay_heap_manager.remove_from_heap(old_object_id)
        self.dataclay_heap_manager._add_to_inmemory_map(dco)

    def remove_from_heap(self, object_id):
        """
        @postcondition: Remove reference from Heap. Even if we remove it from the heap,
        the object won't be Garbage collected till HeapManager flushes the object and releases it.
        @param object_id: id of object to remove from heap
        """
        self.dataclay_heap_manager.remove_from_heap(object_id)

    def get_or_new_volatile_instance_and_load(
        self, object_id, metaclass_id, hint, obj_with_data, ifacebitmaps
    ):
        """
        @postcondition: Get from Heap or create a new volatile in EE and load data on it.
        @param object_id: ID of object to get or create
        @param metaclass_id: ID of class of the object (needed for creating it)
        @param hint: Hint of the object, can be None.
        @param obj_with_data: data of the volatile instance
        @param ifacebitmaps: interface bitmaps
        """
        return self.dataclay_object_loader.get_or_new_volatile_instance_and_load(
            metaclass_id, object_id, hint, obj_with_data, ifacebitmaps
        )

    def add_volatiles_under_deserialization(self, volatiles):
        """
        @postcondition: Add volatiles provided to be 'under deserialization' in case any execution in a volatile is thrown
        before it is completely deserialized. This is needed in case any deserialization depends on another (not for race conditions)
        like hashcodes or other similar cases.
        @param volatiles: volatiles under deserialization
        """
        for vol_obj in volatiles:
            self.volatiles_under_deserialization[vol_obj.object_id] = vol_obj

    def remove_volatiles_under_deserialization(self, volatiles):
        """
        @postcondition: Remove volatiles under deserialization
        """
        for vol_obj in volatiles:
            if vol_obj.object_id in self.volatiles_under_deserialization:
                del self.volatiles_under_deserialization[vol_obj.object_id]

    def get_copy_of_object(self, from_object, recursive):
        session_id = self.get_session().id

        backend_id = from_object.get_location()
        try:
            execution_client = self.ready_clients[backend_id]
        except KeyError:
            exec_env = self.get_execution_environment_info(backend_id)
            execution_client = EEClient(exec_env.hostname, exec_env.port)
            self.ready_clients[backend_id] = execution_client

        copiedObject = execution_client.ds_get_copy_of_object(
            session_id, from_object.get_object_id(), recursive
        )
        result = DeserializationLibUtilsSingleton.deserialize_params_or_return(
            copiedObject, None, None, None, self
        )

        return result[0]

    def update_object(self, into_object, from_object):
        session_id = self.get_session().id

        backend_id = into_object.get_location()
        try:
            execution_client = self.ready_clients[backend_id]
        except KeyError:
            exec_env = self.get_execution_environment_info(backend_id)
            execution_client = EEClient(exec_env.hostname, exec_env.port)
            self.ready_clients[backend_id] = execution_client

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
                    if cur_oid == from_object.get_object_id():
                        new_ids[cur_oid] = into_object.get_object_id()
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

        execution_client.ds_update_object(
            session_id, into_object.get_object_id(), serialized_params
        )

    def get_from_heap(self, object_id):
        """
        @postcondition: Get from heap.
        @param object_id: id of object to get from heap
        @return Object with id provided in heap or None if not found.
        """
        return self.dataclay_heap_manager.get_from_heap(object_id)

    def lock(self, object_id):
        """
        @postcondition: Lock object with ID provided
        @param object_id: ID of object to lock
        """
        self.locker_pool.lock(object_id)

    def unlock(self, object_id):
        """
        @postcondition: Unlock object with ID provided
        @param object_id: ID of object to unlock
        """
        self.locker_pool.unlock(object_id)

    def run_remote(self, object_id, backend_id, operation_name, value):
        session_id = self.get_session().id
        implementation_id = self.get_implementation_id(object_id, operation_name)

        try:
            execution_client = self.ready_clients[backend_id]
        except KeyError:
            exec_env = self.get_execution_environment_info(backend_id)
            execution_client = EEClient(exec_env.hostname, exec_env.port)
            self.ready_clients[backend_id] = execution_client

        operation = self.get_operation_info(object_id, operation_name)
        serialized_params = SerializationLibUtilsSingleton.serialize_params_or_return(
            params=(value,),
            iface_bitmaps=None,
            params_spec=operation.params,
            params_order=operation.paramsOrder,
            hint_volatiles=None,
            runtime=self,
        )

        ret = execution_client.ds_execute_implementation(
            object_id, implementation_id, session_id, serialized_params
        )

        if ret is not None:
            return DeserializationLibUtilsSingleton.deserialize_return(
                ret, None, operation.returnType, self
            )

    def call_execute_to_ds(self, instance, parameters, operation_name, exec_env_id, using_hint):

        object_id = instance.get_object_id()
        operation = self.get_operation_info(object_id, operation_name)
        session_id = self.get_session().id
        implementation_id = self.get_implementation_id(object_id, operation_name)

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
        max_retry = Configuration.MAX_EXECUTION_RETRIES
        num_misses = 0
        executed = False
        for _ in range(max_retry):
            try:
                self.logger.verbose("Obtaining API for remote execution in %s ", exec_env_id)
                execution_client = self.ready_clients[exec_env_id]
            except KeyError:
                exec_env = self.get_execution_environment_info(exec_env_id)
                self.logger.debug(
                    "Not found in cache ExecutionEnvironment {%s}! Starting it at %s:%d",
                    exec_env_id,
                    exec_env.hostname,
                    exec_env.port,
                )
                execution_client = EEClient(exec_env.hostname, exec_env.port)
                self.ready_clients[exec_env_id] = execution_client

            try:
                self.logger.verbose("Calling remote EE %s ", exec_env_id)
                ret = execution_client.ds_execute_implementation(
                    object_id, implementation_id, session_id, serialized_params
                )
                executed = True
                break

            except (DataClayException, RpcError) as dce:
                self.logger.warning("Execution resulted in an error, retrying...", exc_info=dce)

                is_race_condition = False
                if serialized_params is not None and serialized_params.persistent_refs is not None:
                    for param in serialized_params.persistent_refs:
                        if param.object_id in self.volatile_parameters_being_send:
                            is_race_condition = True
                            break
                if not is_race_condition:
                    num_misses = num_misses + 1
                    self.logger.debug("Exception dataclay during execution. Retrying...")
                    self.logger.debug(str(dce))

                    locations = self.get_from_heap(object_id).get_replica_locations()
                    if locations is None or len(locations) == 0:
                        try:
                            locations = self.get_metadata(object_id).locations
                            new_location = False
                        except DataClayException:
                            locations = None

                    if locations is None:
                        self.logger.warning(
                            "Execution failed and no metadata available. Cannot continue"
                        )
                        raise

                    for loc in locations:
                        self.logger.debug("Found location %s" % str(loc))
                        if loc != exec_env_id:
                            exec_env_id = loc
                            self.logger.debug("Found different location %s" % str(loc))
                            new_location = True
                            break

                    if not new_location:
                        exec_env_id = next(iter(locations))
                    if using_hint:
                        instance.set_hint(exec_env_id)
                    self.logger.debug(
                        "[==Miss Jump==] MISS. The object %s was not in the exec.location %s. Retrying execution."
                        % (instance.get_object_id(), str(exec_env_id))
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
                    param_instance = self.get_from_heap(param.object_id)
                    param_instance.set_hint(exec_env_id)
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
            self.logger.debug(f"Result of operation named {operation_name} received: None")
        else:
            self.logger.debug(
                f"Deserializing result of operation named {operation_name}, return type is {operation.returnType.signature}"
            )
            result = DeserializationLibUtilsSingleton.deserialize_return(
                ret, None, operation.returnType, self
            )
            self.logger.debug(
                f"Deserialization of result of operation named {operation_name} successfully finished."
            )
        return result

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
        self.logger.debug(
            f"[==Import_models_from_external_dataclay==] Registering namespace {namespace} from {ext_dataclay_id}"
        )
        self.ready_clients["@LM"].import_models_from_external_dataclay(namespace, ext_dataclay_id)

    def get_by_alias(self, alias, dataset_name):
        oid, class_id, hint = self.ready_clients["@MDS"].get_object_from_alias(
            self.get_session().id, alias, dataset_name
        )
        return self.get_object_by_id(oid, class_id, hint)

    def get_object_location_by_id(self, object_id):
        exec_envs = list(self.get_all_execution_environments_at_dataclay(self.get_dataclay_id()))
        return exec_envs[hash(object_id) % len(exec_envs)]

    def delete_alias_in_dataclay(self, alias, dataset_name):
        self.ready_clients["@MDS"].delete_alias(self.get_session().id, alias, dataset_name)

    @abstractmethod
    def delete_alias(self, dc_obj):
        pass

    def prepare_for_new_replica_version_consolidate(
        self, object_id, object_hint, backend_id, backend_hostname, different_location
    ):
        """
        Helper function to prepare information for new replica - version - consolidate algorithms
        :param object_id: id of the object
        :param backend_id: Destination backend ID to get information from (can be none)
        :param backend_hostname: Destination hostname to get information from (can be null)
        :param different_location: if true indicates that destination backend should be different to any location of the object
        :return: Tuple with destination backend API to call and:
                        Either information of dest backend with id provided, some exec env in host provided or random exec env.
        """

        backend_id_to_call = object_hint
        if backend_id_to_call is None:
            backend_id_to_call = self.get_location(object_id)

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
                        self.get_dataclay_id()
                    )
                    for exec_env_id, exec_env in all_exec_envs.items():
                        self.logger.debug(f"Checking if {exec_env_id} is in {obj_locations}")
                        for obj_location in obj_locations:
                            if str(exec_env_id) != str(obj_location):
                                dest_backend_id = exec_env_id
                                dest_backend = exec_env
                                break
                    if dest_backend is None:
                        self.logger.debug(
                            "Could not find any different location for replica, updating available exec envs"
                        )
                        # retry updating locations
                        all_exec_envs = self.get_all_execution_environments_at_dataclay(
                            self.get_dataclay_id(), force_update=True
                        )
                        for exec_env_id, exec_env in all_exec_envs.items():
                            for obj_location in obj_locations:
                                if str(exec_env_id) != str(obj_location):
                                    dest_backend_id = exec_env_id
                                    dest_backend = exec_env
                                    break
                if dest_backend is None:
                    dest_backend_id = object_hint
                    dest_backend = self.get_execution_environment_info(dest_backend_id)

        else:
            dest_backend = self.get_execution_environment_info(dest_backend_id)

        try:
            execution_client = self.ready_clients[backend_id_to_call]
        except KeyError:
            backend_to_call = self.get_execution_environment_info(backend_id_to_call)
            execution_client = EEClient(backend_to_call.hostname, backend_to_call.port)
            self.ready_clients[backend_id_to_call] = execution_client
        return execution_client, dest_backend

    def new_replica(self, object_id, hint, backend_id, backend_hostname, recursive):
        self.logger.debug(f"Starting new replica of {object_id}")
        # IMPORTANT NOTE: pyclay is not able to replicate/versionate/consolidate Java or other language objects
        session_id = self.get_session().id

        execution_client, dest_backend = self.prepare_for_new_replica_version_consolidate(
            object_id, hint, backend_id, backend_hostname, True
        )
        dest_backend_id = dest_backend.id
        replicated_objs = execution_client.new_replica(
            session_id, object_id, dest_backend_id, recursive
        )
        self.logger.debug(f"Replicated: {replicated_objs} into {dest_backend_id}")
        # Update replicated objects metadata
        for replicated_obj_id in replicated_objs:
            if replicated_obj_id in self.metadata_cache:
                self.metadata_cache[replicated_obj_id].locations.add(dest_backend_id)
            obj = self.get_from_heap(object_id)
            obj.add_replica_location(dest_backend_id)
            if obj.get_origin_location() is None:
                # at client side there cannot be two replicas of same oid
                obj.set_origin_location(hint)
        return dest_backend_id

    def new_version(
        self, object_id, hint, class_id, dataset_name, backend_id, backend_hostname, recursive
    ):
        # IMPORTANT NOTE: pyclay is not able to replicate/versionate/consolidate Java or other language objects
        self.logger.debug(f"Starting new version of {object_id}")
        session_id = self.get_session().id
        execution_client, dest_backend = self.prepare_for_new_replica_version_consolidate(
            object_id, hint, backend_id, backend_hostname, False
        )
        dest_backend_id = dest_backend.id
        version_id = execution_client.new_version(session_id, object_id, dest_backend_id)
        locations = set()
        locations.add(dest_backend_id)
        metadata_info = MetaDataInfo(
            version_id, False, dataset_name, class_id, locations, None, None
        )
        self.metadata_cache[object_id] = metadata_info
        self.logger.debug(f"Finished new version of {object_id}, created version {version_id}")
        return version_id, dest_backend_id

    def consolidate_version(self, version_id, version_hint):
        # IMPORTANT NOTE: pyclay is not able to replicate/versionate/consolidate Java or other language objects
        self.logger.debug(f"Starting consolidate version of {version_id}")
        session_id = self.get_session().id
        backend_id_to_call = version_hint
        if backend_id_to_call is None:
            backend_id_to_call = self.get_location(version_id)

        try:
            execution_client = self.ready_clients[backend_id_to_call]
        except KeyError:
            backend_to_call = self.get_execution_environment_info(backend_id_to_call)
            execution_client = EEClient(backend_to_call.hostname, backend_to_call.port)
            self.ready_clients[backend_id_to_call] = execution_client

        execution_client.consolidate_version(session_id, version_id)
        self.logger.debug(f"Finished consolidate version of {version_id}")

    def move_object(self, instance, source_backend_id, dest_backend_id, recursive):

        object_id = instance.get_object_id()
        moved_objs = self.ready_clients["@LM"].move_object(
            self.get_session().id, object_id, source_backend_id, dest_backend_id, recursive
        )
        for oid in moved_objs:
            if oid in self.metadata_cache:
                del self.metadata_cache[oid]

    def exists_in_dataclay(self, object_id):
        return self.ready_clients["@LM"].object_exists_in_dataclay(object_id)

    def get_num_objects(self):
        return self.ready_clients["@LM"].get_num_objects()

    def exists(self, object_id):
        return self.dataclay_heap_manager.exists_in_heap(object_id)

    def register_external_dataclay(self, exthostname, extport):
        """Register external dataClay for federation
        :param exthostname: external dataClay host name
        :param extport: external dataClay port
        :return: external dataClay ID registered
        :type exthostname: string
        :type extport: int
        :rtype: UUID
        """
        return self.ready_clients["@LM"].register_external_dataclay(exthostname, extport)

    def get_or_new_persistent_instance(self, object_id, metaclass_id, hint):
        """Check if object with ID provided exists in dataClay heap.
        If so, return it. Otherwise, create it.
        :param object_id: ID of object to get or create
        :param metaclass_id: ID of class of the object (needed for creating it)
        :param hint: Hint of the object, can be None.
        :returns: return the instance with object id provided
        :type object_id: ObjectID
        :type metaclass_id: MetaClassID
        :type hint: BackendID
        :rtype: DataClayObject
        """
        # TODO: Remove call to LM and use metaclass name not id
        if metaclass_id is None:
            metadata = self.ready_clients["@LM"].get_metadata_by_oid(
                self.get_session().id, object_id
            )
            metaclass_id = metadata.metaclass_id

        return self.dataclay_object_loader.get_or_new_persistent_instance(
            metaclass_id, object_id, hint
        )

    def get_dataclay_id(self):
        """Get dataClay ID of current dataClay
        :return: ID of current dataclay
        :rtype: UUID
        """
        if self.dataclay_id is None:
            self.dataclay_id = self.ready_clients["@MDS"].get_dataclay_id()
        return self.dataclay_id

    def get_external_dataclay_id(self, exthostname, extport):
        """Get external dataClay ID with host and port identified
        :param exthostname: external dataClay host name
        :param extport: external dataClay port
        :return: None
        :type exthostname: string
        :type extport: int
        :rtype: None
        """
        return self.ready_clients["@LM"].get_external_dataclay_id(exthostname, extport)

    def get_external_dataclay_info(self, dataclay_id):
        """Get external dataClay information
        :param dataclay_id: external dataClay ID
        :return: DataClayInstance information
        :type dataclay_id: UUID
        :rtype: DataClayInstance
        """
        return self.ready_clients["@LM"].get_external_dataclay_info(dataclay_id)

    def get_location(self, object_id):
        self.logger.debug("Looking for location of object %s", str(object_id))
        try:
            obj = self.get_from_heap(object_id)
            if obj is not None:
                hint = obj.get_hint()
                if hint is not None:
                    self.logger.debug("Returning hint from heap object")
                    return hint
                else:
                    raise DataClayException(
                        "The object %s is not initialized well, hint missing or not exist"
                        % object_id
                    )
            else:
                raise DataClayException("The object %s is not initialized" % object_id)
        except DataClayException as e:
            # If the object is not initialized well trying to obtain location from metadata
            metadata = self.get_metadata(object_id)
            return six.advance_iterator(iter(metadata.locations))

    # TODO: Use MetadataService and return ObjectMD
    def get_metadata(self, object_id):
        if object_id in self.metadata_cache:
            metadata = self.metadata_cache[object_id]
            self.logger.debug(f"Object metadata found in cache: {metadata}")
            return metadata
        else:
            metadata = self.ready_clients["@LM"].get_metadata_by_oid(
                self.get_session().id, object_id
            )
            if metadata is None:
                self.logger.debug("Object %s not registered", object_id)
                raise DataClayException("The object %s is not registered" % object_id)
            self.metadata_cache[object_id] = metadata
            self.logger.debug(f"Obtained metadata: {metadata}")
            return metadata

    def remove_metadata_from_cache(self, object_id):
        if object_id in self.metadata_cache:
            del self.metadata_cache[object_id]

    def get_all_locations(self, object_id):
        self.logger.debug("Getting all locations of object %s", object_id)
        locations = set()
        obj = self.get_from_heap(object_id)
        if obj is not None:
            replica_locs = obj.get_replica_locations()
            if replica_locs is not None:
                locations.update(replica_locs)
            if obj.get_origin_location() is not None:
                locations.add(obj.get_origin_location())
        try:
            metadata = self.get_metadata(object_id)
            for loc in metadata.locations:
                locations.add(loc)
            # add hint location
            if obj is not None:
                hint = obj.get_hint()
                if hint is not None:
                    locations.add(hint)

            return locations
        except:
            self.logger.debug("Object %s has no metadata", object_id)
            if obj is not None:
                hint = obj.get_hint()
                if hint is not None:
                    self.logger.debug("Returning list with hint from heap object")
                    locations = dict()
                    locations[hint] = self.get_execution_environment_info(hint)
                    return locations
                else:
                    raise DataClayException(
                        "The object %s is not initialized well, hint missing or not exist"
                        % object_id
                    )
            else:
                raise DataClayException("The object %s is not initialized" % object_id)

    def get_all_execution_environments_info(self, force_update=False):
        if self.ee_info_map is None or self.ee_info_map is not None and force_update:
            self.ee_info_map = self.ready_clients["@MDS"].get_all_execution_environments(
                LANG_PYTHON, from_backend=self.is_exec_env()
            )
            if self.logger.isEnabledFor(TRACE):
                n = len(self.ee_info_map)
                self.logger.trace(
                    "Response of ExecutionEnvironmentsInfo returned #%d ExecutionEnvironmentsInfo",
                    n,
                )
                for i, (ee_id, ee_info) in enumerate(self.ee_info_map.items(), 1):
                    self.logger.trace(
                        "ExecutionEnvironments info (#%d/%d): %s\n%s", i, n, ee_id, ee_info
                    )
                self.logger.trace(
                    "Response of ExecutionEnvironmentsInfo returned #%d ExecutionEnvironmentsInfo",
                    len(self.ee_info_map),
                )

        return self.ee_info_map

    def get_execution_environment_info(self, backend_id):
        exec_envs = self.get_all_execution_environments_info(force_update=False)
        if backend_id in exec_envs:
            return exec_envs[backend_id]
        else:
            exec_envs = self.get_all_execution_environments_info(force_update=True)
            return exec_envs[backend_id]

    def get_all_execution_environments_at_host(self, hostname):
        exec_envs_at_host = dict()
        exec_envs = self.get_all_execution_environments_info(force_update=False)
        for exec_env_id, exec_env in exec_envs.items():
            if exec_env.hostname == hostname:
                exec_envs_at_host[exec_env_id] = exec_env
        if not bool(exec_envs_at_host):
            exec_envs = self.get_all_execution_environments_info(force_update=True)
            for exec_env_id, exec_env in exec_envs.items():
                if exec_env.hostname == hostname:
                    exec_envs_at_host[exec_env_id] = exec_env
        return exec_envs_at_host

    def get_all_execution_environments_at_dataclay(self, dataclay_instance_id, force_update=False):
        exec_envs_at_dataclay_instance_id = dict()
        if not force_update:
            exec_envs = self.get_all_execution_environments_info(force_update=False)
            for exec_env_id, exec_env in exec_envs.items():
                self.logger.debug(
                    f"Checking if {exec_env} belongs to dataclay with id {dataclay_instance_id}"
                )
                if exec_env.dataclay_id == dataclay_instance_id:
                    exec_envs_at_dataclay_instance_id[exec_env_id] = exec_env
        if not bool(exec_envs_at_dataclay_instance_id):
            exec_envs = self.get_all_execution_environments_info(force_update=True)
            for exec_env_id, exec_env in exec_envs.items():
                self.logger.debug(
                    f"Checking if {exec_env} belongs to dataclay with id {dataclay_instance_id}"
                )
                if exec_env.dataclay_id == dataclay_instance_id:
                    exec_envs_at_dataclay_instance_id[exec_env_id] = exec_env
        return exec_envs_at_dataclay_instance_id

    def get_all_execution_environments_with_name(self, dsname):
        exec_envs_with_name = dict()
        exec_envs = self.get_all_execution_environments_info(force_update=False)
        for exec_env_id, exec_env in exec_envs.items():
            if exec_env.sl_name == dsname and exec_env.dataclay_id == self.get_dataclay_id():
                exec_envs_with_name[exec_env_id] = exec_env
        if not bool(exec_envs_with_name):
            exec_envs = self.get_all_execution_environments_info(force_update=True)
            for exec_env_id, exec_env in exec_envs.items():
                if exec_env.sl_name == dsname and exec_env.dataclay_id == self.get_dataclay_id():
                    exec_envs_with_name[exec_env_id] = exec_env
        return exec_envs_with_name

    def get_execution_environments_names(self, force_update=False):
        exec_envs_names = list()
        exec_envs = self.get_all_execution_environments_info(force_update=force_update)
        for exec_env_id, exec_env in exec_envs.items():
            if exec_env.dataclay_id == self.get_dataclay_id():
                exec_envs_names.append(exec_env.sl_name)
        if self.logger.isEnabledFor(TRACE):
            n = len(exec_envs_names)
            self.logger.trace(
                "Response of ExecutionEnvironmentsInfo returned #%d ExecutionEnvironmentsInfo", n
            )
        return exec_envs_names

    def choose_location(self, instance):
        """Choose execution/make persistent location.
        :param instance: Instance to use in call
        :param alias: The alias of the instance
        :returns: Location
        :type instance: DataClayObject
        :rtype: DataClayID
        """

        exec_env_id = self.get_object_location_by_id(instance.get_object_id())
        instance.set_hint(exec_env_id)
        self.logger.verbose("ExecutionEnvironmentID obtained for execution = %s", exec_env_id)
        return exec_env_id

    def activate_tracing(self, initialize):
        """Activate tracing"""
        initialize_extrae(initialize)

    def deactivate_tracing(self, finalize_extrae):
        """Close the runtime paraver manager and deactivate the traces in LM (That deactivate also the DS)"""
        finish_tracing(finalize_extrae)

    def activate_tracing_in_dataclay_services(self):
        """Activate the traces in LM (That activate also the DS)"""
        if extrae_tracing_is_enabled():
            self.ready_clients["@LM"].activate_tracing(get_current_available_task_id())

    def deactivate_tracing_in_dataclay_services(self):
        """Deactivate the traces in LM and DSs"""
        if extrae_tracing_is_enabled():
            self.ready_clients["@LM"].deactivate_tracing()

    def get_traces_in_dataclay_services(self):
        """Get temporary traces from LM and DSs and store it in current workspace"""
        traces = self.ready_clients["@LM"].get_traces()
        traces_dir = Configuration.TRACES_DEST_PATH
        if len(traces) > 0:
            set_path = Configuration.TRACES_DEST_PATH + "/set-0"
            trace_mpits = Configuration.TRACES_DEST_PATH + "/TRACE.mpits"
            with open(trace_mpits, "a+") as trace_file:
                # store them here
                for key, value in traces.items():
                    dest_path = set_path + "/" + key
                    self.logger.debug("Storing object %s" % dest_path)
                    with open(dest_path, "wb") as dest_file:
                        dest_file.write(value)
                        dest_file.close()
                    if key.endswith("mpit"):
                        pointer = str(dest_path) + " named\n"
                        trace_file.write(pointer)
                        self.logger.debug("Appending to %s line: %s" % (trace_mpits, pointer))
                trace_file.flush()
                trace_file.close()

    def heap_size(self):
        return self.dataclay_heap_manager.heap_size()

    def count_loaded_objs(self):
        return self.dataclay_heap_manager.count_loaded_objs()

    def stop_gc(self):
        """
        @postcondition: stop GC. useful for shutdown.
        """
        # Stop HeapManager
        self.logger.debug("Stopping GC. Sending shutdown event.")
        self.dataclay_heap_manager.shutdown()
        self.logger.debug("Waiting for GC.")
        self.dataclay_heap_manager.join()
        self.logger.debug("GC stopped.")

    def stop_runtime(self):
        """
        @postcondition: Stop connections and daemon threads.
        """

        self.logger.verbose("** Stopping runtime **")

        for name, client in self.ready_clients.items():
            self.logger.verbose("Closing client connection to %s", name)
            client.close()

        self.ready_clients = {}

        # Stop HeapManager
        self.stop_gc()
        self.dataclay_id = None

    ################## EXTRAE IGNORED FUNCTIONS ###########################
    deactivate_tracing.do_not_trace = True
    activate_tracing.do_not_trace = True
    activate_tracing_in_dataclay_services.do_not_trace = True
    deactivate_tracing_in_dataclay_services.do_not_trace = True
