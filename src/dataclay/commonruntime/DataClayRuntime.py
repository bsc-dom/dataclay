""" Class description goes here. """
import importlib
import uuid
import six
import os
import logging
import traceback
from abc import ABCMeta, abstractmethod
from logging import TRACE
from lru import LRU
from grpc import RpcError
from dataclay.heap.LockerPool import LockerPool
from dataclay.communication.grpc.messages.common.common_messages_pb2 import LANG_PYTHON
from dataclay.paraver import extrae_tracing_is_enabled, initialize_extrae, get_current_available_task_id, \
    finish_tracing, get_task_id
from dataclay.communication.grpc.clients.ExecutionEnvGrpcClient import EEClient
from dataclay.communication.grpc.clients.LogicModuleGrpcClient import LMClient
from dataclay.commonruntime.Runtime import threadLocal
from dataclay.serialization.lib.DeserializationLibUtils import DeserializationLibUtilsSingleton
from dataclay.serialization.lib.SerializationLibUtils import SerializationLibUtilsSingleton
from dataclay.exceptions.exceptions import DataClayException
from dataclay.util import Configuration

class NULL_NAMESPACE:
    """null Namespace for uuid3, same as java's UUID.nameUUIDFromBytes"""
    bytes = b''

@six.add_metaclass(ABCMeta)
class DataClayRuntime(object):
        
    """ Logger """ 
    logger = logging.getLogger('dataclay.api')

    def __init__(self):
        """ Cache of alias """
        # TODO: un-hardcode this
        self.alias_cache = LRU(50000)
        
        """ Cache of EE info """
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
        
        # Local info of thread
        self.thread_local_info = threadLocal
        
        """ Cache of metadata """
        self.metadata_cache = LRU(50)
        
    @abstractmethod
    def initialize_runtime_aux(self): pass
    
    def initialize_runtime(self):
        """ 
        IMPORTANT: getRuntime can be called from decorators, during imports, and therefore a runtime might be created. 
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
        
    @abstractmethod
    def is_exec_env(self):
        """
        @return: TRUE if runtime is for EE. False otherwise.
        """
        pass
    
    @abstractmethod
    def get_session_id(self):
        """ Get session id.
        :returns: session id
        :rtype: uuid
        """
        pass
    
    def get_lm_api(self, host, port):
        """ Get logic module connection.
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
    def get_operation_info(self, object_id, operation_name): pass
  
    @abstractmethod
    def get_implementation_id(self, object_id, operation_name, implementation_idx=0): pass
    
    def get_object_by_id(self, object_id, class_id=None, hint=None):
        """ Get object instance directly from an object id, use class id and hint in 
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
        self.logger.debug("Get object %s by id", str(object_id))
        o = self.get_from_heap(object_id)
        if o is not None:
            return o

        if not class_id:
            full_name, namespace = self.ready_clients["@LM"].get_object_info(
                self.get_session_id(), object_id)
            self.logger.debug("Trying to import full_name: %s from namespace %s",
                         full_name, namespace)

            # Rearrange the division, full_name may include dots (and be nested)
            prefix, class_name = ("%s.%s" % (namespace, full_name)).rsplit('.', 1)
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
        
    def get_or_new_volatile_instance_and_load(self, object_id, metaclass_id, hint,
                                              obj_with_data, ifacebitmaps):
        """
        @postcondition: Get from Heap or create a new volatile in EE and load data on it.
        @param object_id: ID of object to get or create 
        @param metaclass_id: ID of class of the object (needed for creating it) 
        @param hint: Hint of the object, can be None. 
        @param obj_with_data: data of the volatile instance 
        @param ifacebitmaps: interface bitmaps
        """ 
        return self.dataclay_object_loader.get_or_new_volatile_instance_and_load(metaclass_id, object_id, hint, obj_with_data, ifacebitmaps)
    
    def add_volatiles_under_deserialization(self, volatiles):
        """
        @postcondition: Add volatiles provided to be 'under deserialization' in case any execution in a volatile is thrown 
        before it is completely deserialized. This is needed in case any deserialization depends on another (not for race conditions)
        like hashcodes or other similar cases.
        @param volatiles: volatiles under deserialization
        """
        self.thread_local_info.volatiles_under_deserialitzation = volatiles
   
    def remove_volatiles_under_deserialization(self):
        """
        @postcondition: Remove volatiles under deserialization
        """
        self.thread_local_info.volatiles_under_deserialitzation = None
        
    def get_copy_of_object(self, from_object, recursive):
        session_id = self.get_session_id()
        
        backend_id = from_object.get_location()
        try:
            execution_client = self.ready_clients[backend_id]
        except KeyError:
            exeenv = self.get_execution_environments_info()[backend_id]
            execution_client = EEClient(exeenv.hostname, exeenv.port)
            self.ready_clients[backend_id] = execution_client
        
        copiedObject = execution_client.ds_get_copy_of_object(session_id, from_object.get_object_id(), recursive)
        result = DeserializationLibUtilsSingleton.deserialize_params_or_return(copiedObject, None, None, None, self)
            
        return result[0]            
        
    def update_object(self, into_object, from_object):
        session_id = self.get_session_id()
        
        backend_id = into_object.get_location()
        try:
            execution_client = self.ready_clients[backend_id]
        except KeyError:
            exeenv = self.get_execution_environments_info()[backend_id]
            execution_client = EEClient(exeenv.hostname, exeenv.port)
            self.ready_clients[backend_id] = execution_client
        
        # We serialize objects like volatile parameters
        parameters = list()
        parameters.append(from_object)
        # TODO: modify serialize_params_or_return to not require this
        params_order = list()
        params_order.append("object")
        params_spec = dict()
        params_spec["object"] = "DataClayObject"  # not used, see serialized_params_or_return
        ser_from = SerializationLibUtilsSingleton.serialize_params_or_return(
            params=parameters,
            iface_bitmaps=None,
            params_spec=params_spec,
            params_order=params_order,
            hint_volatiles=backend_id,
            runtime=self,
            recursive=True,
            for_update=True)
        
        vol_objects = ser_from[3]
        if vol_objects is not None:
            new_ids = dict()
            
            for tag in vol_objects:
                cur_oid = ser_from[3][tag][0]
                if cur_oid not in new_ids:
                    if cur_oid == from_object.get_object_id():
                        new_ids[cur_oid] = into_object.get_object_id()
                    else:
                        new_ids[cur_oid] = uuid.uuid4()
                
                ser_from[3][tag] = (new_ids[cur_oid],) + ser_from[3][tag][1:]
            
            for vol_tag in vol_objects:
                oids = ser_from[3][vol_tag][2][0]
                for tag, oid in oids.items():
                    if oid in new_ids:
                        try:
                            ser_from[3][vol_tag][2][0][tag] = new_ids[oid]
                        except KeyError: 
                            pass
        
        self.logger.debug("Sending updated metadata: %s", str(ser_from))

        execution_client.ds_update_object(session_id, into_object.get_object_id(), ser_from)
        
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
        session_id = self.get_session_id()
        implementation_id = self.get_implementation_id(object_id, operation_name)

        try:
            execution_client = self.ready_clients[backend_id]
        except KeyError:
            exeenv = self.get_execution_environments_info()[backend_id]
            execution_client = EEClient(exeenv.hostname, exeenv.port)
            self.ready_clients[backend_id] = execution_client

        operation = self.get_operation_info(object_id, operation_name)
        value = SerializationLibUtilsSingleton.serialize_params_or_return(
            params=(value,),
            iface_bitmaps=None,
            params_spec=operation.params,
            params_order=operation.paramsOrder,
            hint_volatiles=None,
            runtime=self
        )

        ret = execution_client.ds_execute_implementation(object_id, implementation_id,
            session_id, value)

        if ret is not None:
            self.logger.trace("Execution return %s of type %s", ret, operation.returnType)
            return DeserializationLibUtilsSingleton.deserialize_return(ret, None, operation.returnType, self)
        
    def call_execute_to_ds(self, instance, parameters, operation_name, exeenv_id, using_hint):
        
        object_id = instance.get_object_id()
        operation = self.get_operation_info(object_id, operation_name)
        session_id = self.get_session_id()
        implementation_id = self.get_implementation_id(object_id, operation_name)

        # // === SERIALIZE PARAMETERS === //
        serialized_params = SerializationLibUtilsSingleton.serialize_params_or_return(
            params=parameters,
            iface_bitmaps=None,
            params_spec=operation.params,
            params_order=operation.paramsOrder,
            hint_volatiles=exeenv_id,
            runtime=self)
        
        if serialized_params is not None and serialized_params[3] is not None:
            for param in serialized_params[3].values():
                self.volatile_parameters_being_send.add(param[0])
            
        # // === EXECUTE === //
        max_retry = Configuration.MAX_EXECUTION_RETRIES
        num_misses = 0
        executed = False
        for _ in range(max_retry):
            try:
                self.logger.verbose("Obtaining API for remote execution in %s ", exeenv_id)
                execution_client = self.ready_clients[exeenv_id]
            except KeyError:
                exeenv = self.get_execution_environments_info()[exeenv_id] 
                self.logger.debug("Not found in cache ExecutionEnvironment {%s}! Starting it at %s:%d",
                               exeenv_id, exeenv.hostname, exeenv.port)
                execution_client = EEClient(exeenv.hostname, exeenv.port)
                self.ready_clients[exeenv_id] = execution_client
    
            try:
                self.logger.verbose("Calling remote EE %s ", exeenv_id)
                ret = execution_client.ds_execute_implementation(
                    object_id,
                    implementation_id,
                    session_id,
                    serialized_params)
                executed = True
                break
            
            except (DataClayException, RpcError) as dce:
                self.logger.warning("Execution resulted in an error, retrying...", exc_info=dce)

                is_race_condition = False
                if serialized_params is not None and serialized_params[4] is not None:
                    for param in serialized_params[4]:
                        if param.get_object_id() in self.volatile_parameters_being_send:
                            is_race_condition = True
                            break
                if not is_race_condition:
                    num_misses = num_misses + 1
                    self.logger.debug("Exception dataclay during execution. Retrying...")
                    self.logger.debug(str(dce))
                    if object_id in self.metadata_cache:   
                        del self.metadata_cache[object_id]

                    try:
                        metadata = self.get_metadata(object_id)
                        new_location = False
                    except DataClayException:
                        metadata = None
    
                    if metadata is None:
                        self.logger.warning("Execution failed and no metadata available. Cannot continue")
                        raise
    
                    for loc in metadata.locations:
                        self.logger.debug("Found location %s" % str(loc))
                        if loc != exeenv_id:
                            exeenv_id = loc
                            self.logger.debug("Found different location %s" % str(loc))
                            new_location = True
                            break
                        
                    if not new_location: 
                        exeenv_id = next(iter(metadata.locations))
                
                    if using_hint:
                        instance.set_hint(exeenv_id)
                    
                    self.logger.debug("[==Miss Jump==] MISS. The object %s was not in the exec.location %s. Retrying execution." 
                                % (instance.get_object_id(), str(exeenv_id)));
    
        self.logger.verbose("Result of operation named '%s' received", operation_name)
        if serialized_params is not None and serialized_params[3] is not None:
            for param in serialized_params[3].values():
                if num_misses > 0: 
                    #===========================================================
                    # if there was a miss, it means that the persistent object in which we were executing 
                    # was not in the choosen location. As you can see in the serialize parameters function above
                    # we provide the execution environment as hint to set to volatile parameters. In EE, before
                    # deserialization of volatiles we check if the persistent object in which to execute a method is
                    # there, if not, EE raises and exception. Therefore, if there was a miss, we know that the 
                    # hint we set in volatile parameters is wrong, because they are going to be deserialized/stored
                    # in the same location as the object with the method to execute
                    #===========================================================
                    param_instance = self.get_from_heap(param[0])
                    param_instance.set_hint(exeenv_id)
                self.volatile_parameters_being_send.remove(param[0])
    
        if not executed: 
            raise RuntimeError("[dataClay] ERROR: Trying to execute remotely object  but something went wrong. "
                               "Maybe the object is still not stored (in case of asynchronous makepersistent) and "
                               "waiting time is not enough. Maybe the object does not exist anymore due to a remove. "
                               "Or Maybe an exception happened in the server and the call failed.")
    
        if ret is None:
            return None
        else:
            return DeserializationLibUtilsSingleton.deserialize_return(ret, None, operation.returnType, self)
    
    def synchronize_federated(self, instance, params, operation_name, dc_info_id):
        self.logger.debug("Calling external dataClay to run %s operation in object %s"
                          , operation_name, instance.get_object_id())
        operation = self.get_operation_info(instance.get_object_id(), operation_name)
        implementation_id = self.get_implementation_id(instance.get_object_id(), operation_name)
        # === SERIALIZE PARAMETERS === 
        # Between DC - DC , ifaceBitMaps = null
        serialized_params = SerializationLibUtilsSingleton.serialize_params_or_return(
            params=params,
            iface_bitmaps=None,
            params_spec=operation.params,
            params_order=operation.paramsOrder,
            hint_volatiles=instance.get_hint(),
            runtime=self)
        
        dc_info = self.get_external_dataclay_info(dc_info_id)
        hosts = dc_info.hosts 
        ports = dc_info.ports 
        for i in range(0, len(hosts)):
            try:
                lm_client = self.get_lm_api(hosts[i], ports[i])
                self.logger.debug("[==JUMP==] Request execution to external dataClay %s with host %s and port %s for object %s"
                                  , dc_info_id, hosts[i], ports[i], instance.get_object_id())

                lm_client.synchronize_federated_object(self.get_dataclay_id(), instance.get_object_id(),
                                               implementation_id, serialized_params)     
            except:
                traceback.print_exc()
                if i + 1 == len(hosts):
                    raise RuntimeError("[dataClay] ERROR: Cannot connect to external dataClay with ID %s" % (str(dc_info_id)))
        
    def ensure_object_is_registered(self, session_id, object_id, class_id, hint):
        """ 
        Ensure registration of an object. new replica/version/consolidate/move
        algorithms should not require registered metadata in LogicModule since
        new make persistent implementation behaves like volatiles and metadata
        is created eventually, not synchronously. Currently, we try to register
        it and if it is already registered, just continue.
        :param session_id: ID of session registering object
        :param object_id: ID of object to register
        :param class_id: ID of class of the object
        :param hint: Hint of the object
        :returns: None
        :type session_id: dataClay ID
        :type object_id: dataClay ID
        :type class_id: dataClay ID
        :type hint: dataClay ID
        :rtype: None
        """
        # FIXME: new replica/version/consolidate/move algorithms should not require
        # registered metadata in LogicModule since new make persistent implementation
        # behaves like volatiles and metadata is created eventually, not synchronously.
        # Currently, we try to register it and if it is already registered, just continue.
        # Make sure object is registered.
        # DataSet is None since it is obtained from session at LM.
        reg_info = [object_id, class_id, session_id, None]
        # In next call, alias must be null
        # NOTE: LogicModule register object function does not return an exception for already registered
        # object. We should never call registerObject for already registered objects and that's dataClay
        # code (check isPendingToRegister in EE or isPersistent,.. see makePersistent), and remember that,
        # this is a workaround, registerObject should never be called for replica/version/consolidate algorithms,
        # we must change the algorithms to not depend on metadata.
        # Also, location in which to register the object is the hint (in case it is not registered yet).
        try:
            self.ready_clients["@LM"].register_object(reg_info, hint, None, LANG_PYTHON)
        except:
            pass
    
    def federate_object(self, object_id, ext_dataclay_id, recursive, class_id, hint):
        session_id = self.get_session_id()
        self.logger.debug("[==FederateObject==] Starting federation of object %s with dataClay %s, and session %s", object_id, ext_dataclay_id, session_id)
        self.ensure_object_is_registered(session_id, object_id, class_id, hint)
        self.ready_clients["@LM"].federate_object(session_id, object_id, ext_dataclay_id, recursive)
    
    def unfederate_object(self, object_id, ext_dataclay_id, recursive):
        session_id = self.get_session_id()
        self.logger.debug("[==UnfederateObject==] Starting unfederation of object %s with dataClay %s, and session %s", object_id, ext_dataclay_id, session_id)
        self.ready_clients["@LM"].unfederate_object(session_id, object_id, ext_dataclay_id, recursive)
        # FIXME: ALIAS CACHE SHOULD BE UPDATED FOR OBJECTS WITH ALIAS REMOVED?

    def unfederate_all_objects(self, ext_dataclay_id):
        session_id = self.get_session_id()
        self.logger.debug("[==UnfederateAllObjects==] Starting unfederation of all objects with dataClay %s, and session %s", ext_dataclay_id, session_id)
        self.ready_clients["@LM"].unfederate_all_objects(session_id, ext_dataclay_id)
        # FIXME: ALIAS CACHE SHOULD BE UPDATED FOR OBJECTS WITH ALIAS REMOVED?

    def unfederate_all_objects_with_all_dcs(self):
        session_id = self.get_session_id()
        self.logger.debug("[==UnfederateAllObjectsWithAllDCs==] Starting unfederation of all objects with all dcs, and session %s", session_id)
        self.ready_clients["@LM"].unfederate_all_objects_with_all_dcs(session_id)
        # FIXME: ALIAS CACHE SHOULD BE UPDATED FOR OBJECTS WITH ALIAS REMOVED?
        
    def unfederate_object_with_all_dcs(self, object_id, recursive):
        session_id = self.get_session_id()
        self.logger.debug("[==UnfederateObjectWithAllDCs==] Starting unfederation of object with all dcs, and session %s", session_id)
        self.ready_clients["@LM"].unfederate_object_with_all_dcs(session_id, object_id, recursive)
        # FIXME: ALIAS CACHE SHOULD BE UPDATED FOR OBJECTS WITH ALIAS REMOVED?
    
    def migrate_federated_objects(self, origin_dataclay_id, dest_dataclay_id):
        session_id = self.get_session_id()
        self.logger.debug("[==MigrateFederatedObjects==] Starting migration of federated objects using session %s", session_id)
        self.ready_clients["@LM"].migrate_federated_objects(session_id, origin_dataclay_id, dest_dataclay_id)
        # FIXME: ALIAS CACHE SHOULD BE UPDATED FOR OBJECTS WITH ALIAS REMOVED?
    
    def federate_all_objects(self, dest_dataclay_id):
        session_id = self.get_session_id()
        self.logger.debug("[==FederateAllObjects==] Starting federation of all my objects using session %s", session_id)
        self.ready_clients["@LM"].federate_all_objects(session_id, dest_dataclay_id)
        # FIXME: ALIAS CACHE SHOULD BE UPDATED FOR OBJECTS WITH ALIAS REMOVED?

    def import_models_from_external_dataclay(self, namespace, ext_dataclay_id) -> None:
        """ Import models in namespace specified from an external dataClay
        :param namespace: external dataClay namespace to get
        :param ext_dataclay_id: external dataClay ID
        :return: None
        :type namespace: string
        :type ext_dataclay_id: UUID
        :rtype: None
        """
        self.logger.debug(f"[==Import_models_from_external_dataclay==] Registering namespace {namespace} from {ext_dataclay_id}")
        self.ready_clients["@LM"].import_models_from_external_dataclay(namespace, ext_dataclay_id)

    def get_by_alias(self, alias, class_id, safe=True):
        if safe:
            oid, class_id, hint = self.ready_clients["@LM"].get_object_from_alias(self.get_session_id(), alias)
            return self.get_object_by_id(oid, class_id, hint)

        if alias in self.alias_cache :
            oid, class_id, hint = self.alias_cache[alias]
        else:
            oid = self.get_object_id_by_alias(alias)
            class_id = class_id
            hint = self.get_object_location_by_id(oid)
            self.logger.debug("Added alias %s to cache", alias)
            self.alias_cache[alias] = oid, class_id, hint

        return self.get_object_by_id(oid, class_id, hint)
    
    def get_object_id_by_alias(self, alias):
        return uuid.uuid3(NULL_NAMESPACE, alias)
    
    def get_object_location_by_id(self, object_id):
        exec_envs = list(self.get_execution_environments_info())
        return exec_envs[hash(object_id) % len(exec_envs)]
    
    def get_object_location_by_alias(self, alias):
        return self.get_object_location_by_id(self.get_object_id_by_alias(alias))
    
    def delete_alias(self, alias):
        self.ready_clients["@LM"].delete_alias(self.get_session_id(), alias)
        self.logger.debug("Removing from cache alias %s", alias)     
        if alias in self.alias_cache :   
            del self.alias_cache[alias]
    
    def new_replica(self, object_id, class_id, hint, backend_id, recursive):
        self.logger.debug("Starting new replica")
        session_id = self.get_session_id()
        DataClayRuntime.ensure_object_is_registered(self, session_id, object_id, class_id, hint)
        result = self.ready_clients["@LM"].new_replica(session_id, object_id, backend_id, recursive)
        if object_id in self.metadata_cache :   
            del self.metadata_cache[object_id]
        return result
    
    def new_version(self, object_id, class_id, hint, backend_id):
        self.logger.debug("Starting new version")
        session_id = self.get_session_id()
        DataClayRuntime.ensure_object_is_registered(self, session_id, object_id, class_id, hint)
        result = self.ready_clients["@LM"].new_version(session_id, object_id, backend_id)
        if object_id in self.metadata_cache :   
            del self.metadata_cache[object_id]
        return result
    
    def consolidate_version(self, version_info):
        session_id = self.get_session_id()
        return self.ready_clients["@LM"].consolidate_version(session_id, version_info)
    
    def move_object(self, instance, source_backend_id, dest_backend_id, recursive):
        self.logger.debug("Moving object %r from %s to %s",
                     instance, source_backend_id, dest_backend_id)
        object_id = instance.get_object_id()
        moved_objs = self.ready_clients["@LM"].move_object(self.get_session_id(), object_id,
                            source_backend_id, dest_backend_id, recursive)
        for oid in moved_objs:
            if oid in self.metadata_cache :   
                del self.metadata_cache[oid]
    
    def exists(self, object_id):
        return self.dataclay_heap_manager.exists_in_heap(object_id)
    
    def register_external_dataclay(self, exthostname, extport):
        """ Register external dataClay for federation
        :param exthostname: external dataClay host name
        :param extport: external dataClay port
        :return: external dataClay ID registered
        :type exthostname: string
        :type extport: int
        :rtype: UUID
        """
        return self.ready_clients["@LM"].register_external_dataclay(exthostname, extport)
    
    def get_or_new_persistent_instance(self, object_id, metaclass_id, hint):
        """ Check if object with ID provided exists in dataClay heap.
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
        if metaclass_id is None:
            metadata = self.ready_clients["@LM"].get_metadata_by_oid(
                self.get_session_id(), object_id)
            metaclass_id = metadata.metaclassID

        return self.dataclay_object_loader.get_or_new_persistent_instance(metaclass_id, object_id, hint)
    
    def get_dataclay_id(self):
        """ Get dataClay ID of current dataClay
        :return: ID of current dataclay
        :rtype: UUID
        """
        return self.ready_clients["@LM"].get_dataclay_id()
    
    def get_external_dataclay_id(self, exthostname, extport):
        """ Get external dataClay ID with host and port identified
        :param exthostname: external dataClay host name
        :param extport: external dataClay port
        :return: None
        :type exthostname: string
        :type extport: int
        :rtype: None
        """
        return self.ready_clients["@LM"].get_external_dataclay_id(exthostname, extport)
    
    def get_external_dataclay_info(self, dataclay_id):
        """ Get external dataClay information
        :param dataclay_id: external dataClay ID
        :return: DataClayInstance information
        :type dataclay_id: UUID
        :rtype: DataClayInstance
        """
        return self.ready_clients["@LM"].get_external_dataclay_info(dataclay_id)
    
    def get_dataclays_object_is_federated_with(self, object_id):
        """ Retrieve dataClay instance ids where the object is federated
        :param object_id: ID of the object
        :return: dataClay instance ids where this object is federated
        :type object_id: UUID
        :rtype: set of UUID
        """
        return self.ready_clients["@LM"].get_dataclays_object_is_federated_with(object_id)
    
    def get_external_source_of_dataclay_object(self, object_id):
        """ Retrieve dataClay instance id where the object comes from or NULL
        :param object_id: ID of the object
        :return: dataClay instance ids where this object is federated
        :type object_id: UUID
        :rtype: UUID
        """
        return self.ready_clients["@LM"].get_external_source_of_dataclay_object(object_id)

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
                    raise DataClayException("The object %s is not initialized well, hint missing or not exist" % object_id)
            else:
                raise DataClayException("The object %s is not initialized" % object_id)
        except DataClayException as e:
            # If the object is not initialized well trying to obtain location from metadata
            metadata = self.get_metadata(object_id)
            return six.advance_iterator(iter(metadata.locations))

    def get_metadata(self, object_id):
        if object_id in self.metadata_cache:
            self.logger.debug("Object %s metadata found in cache", object_id)
            metadata = self.metadata_cache[object_id]
        else:
            metadata = self.ready_clients["@LM"].get_metadata_by_oid(
                    self.get_session_id(), object_id)
            if metadata is None: 
                self.logger.debug("Object %s not registered", object_id)
                raise DataClayException("The object %s is not registered" % object_id)
            self.metadata_cache[object_id] = metadata
            self.logger.debug("Received the following MetaDataInfo for object %s: %s",
                    object_id, metadata)
        return metadata

    def get_all_locations(self, object_id):
        self.logger.debug("Getting all locations of object %s", object_id)
        try:
            metadata = self.get_metadata(object_id)
            return metadata.locations
        except:
            self.logger.debug("Object %s has not metadata", object_id)
            obj = self.get_from_heap(object_id)
            if obj is not None:
                hint = obj.get_hint()
                if hint is not None:
                    self.logger.debug("Returning list with hint from heap object")
                    locations = dict()
                    locations[hint] = self.get_execution_environments_info()[hint]
                    return locations
                else:
                    raise DataClayException("The object %s is not initialized well, hint missing or not exist" % object_id)
            else:
                raise DataClayException("The object %s is not initialized" % object_id)

    def get_execution_environments_info(self):
        if self.ee_info_map is None:
            self.ee_info_map = self.ready_clients["@LM"].get_execution_environments_info(self.get_session_id(), LANG_PYTHON,
                                                                                         not self.is_exec_env())
            if self.logger.isEnabledFor(TRACE):
                n = len(self.ee_info_map)
                self.logger.trace("Response of ExecutionEnvironmentsInfo returned #%d ExecutionEnvironmentsInfo", n)
                for i, (ee_id, ee_info) in enumerate(self.ee_info_map.items(), 1):
                    self.logger.trace("ExecutionEnvironments info (#%d/%d): %s\n%s", i, n, ee_id, ee_info)
                self.logger.trace("Response of ExecutionEnvironmentsInfo returned #%d ExecutionEnvironmentsInfo", len(self.ee_info_map))

        return self.ee_info_map

    def get_execution_environments_names(self, username, password):
        credential = (None, password)
        user_id = self.ready_clients["@LM"].get_account_id(username)
        ee_names = self.ready_clients["@LM"].get_execution_environments_names(user_id, credential, LANG_PYTHON)
        if self.logger.isEnabledFor(TRACE):
            n = len(ee_names)
            self.logger.trace("Response of ExecutionEnvironmentsInfo returned #%d ExecutionEnvironmentsInfo", n)
            
        return ee_names

    def choose_location(self, instance, alias=None):
        """ Choose execution/make persistent location.
        :param instance: Instance to use in call
        :param alias: The alias of the instance
        :returns: Location
        :type instance: DataClayObject
        :rtype: DataClayID
        """

        if alias:
            exec_env_id = self.get_object_location_by_id(self.get_object_id_by_alias(alias))
        else:
            exec_env_id = self.get_object_location_by_id(instance.get_object_id())
        instance.set_hint(exec_env_id)
        self.logger.verbose("ExecutionEnvironmentID obtained for execution = %s", exec_env_id)
        return exec_env_id

    def activate_tracing(self, initialize):
        """ Activate tracing """ 
        initialize_extrae(initialize)

    def deactivate_tracing(self, finalize_extrae):
        """Close the runtime paraver manager and deactivate the traces in LM (That deactivate also the DS)"""
        finish_tracing(finalize_extrae)

    def activate_tracing_in_dataclay_services(self):
        """Activate the traces in LM (That activate also the DS) """
        if extrae_tracing_is_enabled():
            self.ready_clients["@LM"].activate_tracing(get_current_available_task_id())

    def deactivate_tracing_in_dataclay_services(self):
        """Deactivate the traces in LM and DSs """
        if extrae_tracing_is_enabled():
            self.ready_clients["@LM"].deactivate_tracing()

    def get_traces_in_dataclay_services(self):
        """ Get temporary traces from LM and DSs and store it in current workspace """
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
        
    ################## EXTRAE IGNORED FUNCTIONS ###########################
    deactivate_tracing.do_not_trace = True
    activate_tracing.do_not_trace = True
    activate_tracing_in_dataclay_services.do_not_trace = True 
    deactivate_tracing_in_dataclay_services.do_not_trace = True 
        
