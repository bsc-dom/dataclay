
""" Class description goes here. """

from io import BytesIO
import logging
import lru
import uuid
import traceback
import time
import os
from dataclay.DataClayObject import DataClayObject
from dataclay.commonruntime.Runtime import getRuntime, setRuntime
from dataclay.commonruntime.Runtime import threadLocal
from dataclay.commonruntime.Settings import settings
from dataclay.communication.grpc.clients.ExecutionEnvGrpcClient import EEClient
from dataclay.communication.grpc.clients.LogicModuleGrpcClient import LMClient
from dataclay.communication.grpc.messages.common.common_messages_pb2 import LANG_PYTHON
from dataclay.paraver import set_current_available_task_id, initialize_extrae, finish_tracing, \
    get_traces, extrae_tracing_is_enabled
from dataclay.DataClayObjProperties import DCLAY_GETTER_PREFIX
from dataclay.DataClayObjProperties import DCLAY_PROPERTY_PREFIX
from dataclay.DataClayObjProperties import DCLAY_SETTER_PREFIX
from dataclay.serialization.lib.DeserializationLibUtils import DeserializationLibUtilsSingleton
from dataclay.serialization.lib.SerializationLibUtils import SerializationLibUtilsSingleton
from dataclay.util.FileUtils import deploy_class
from dataclay.util.classloaders import ClassLoader
from dataclay.util.YamlParser import dataclay_yaml_load
from dataclay.commonruntime.ExecutionEnvironmentRuntime import ExecutionEnvironmentRuntime
from ctypes import c_void_p
from dataclay.util import Configuration

__author__ = 'Alex Barcelo <alex.barcelo@bsc.es>'
__copyright__ = '2015 Barcelona Supercomputing Center (BSC-CNS)'

logger = logging.getLogger(__name__)


class ExecutionEnvironment(object):

    def __init__(self, theee_name):
        self.runtime = ExecutionEnvironmentRuntime(self)
        self.ee_name = theee_name
        """ Initialize runtime """
        self.runtime.initialize_runtime()
            # TODO: de-hardcode this value
        self.cached_sessioninfo = lru.LRU(50)
        self.logger = logging.getLogger(__name__)            
        # This variable will store the following:
        #   - iface_bm (Interface BitMap): used across calls
        #   - session_id (SessionID): is maintained during a deep call
        #   - dataset_id (DataSetID): set on executeImplementation and newPersistentInstance,
        #                             and used for makePersistent of instances.
        self.thread_local_info = threadLocal
        self.init_ee_info()
        
    def init_ee_info(self):
        """
        Initialize EE information (ID). Try to find information in stored files first, otherwise create EE ID. 
        """
        info_file = Configuration.EE_PERSISTENT_INFO_PATH + "infoEE" + self.ee_name
        exists = os.path.isfile(info_file)
        self.logger.info("Reading EE info from %s" % str(info_file))
        if exists:
            fh = open(info_file, 'r+')
            line = fh.readline()
            self.logger.info("READ LINE %s" % str(line))
            self.execution_environment_id = uuid.UUID(line.strip())
            self.logger.info("Initialized EE from file with ID: %s" % str(self.execution_environment_id))
            fh.close()
            
        else:
            self.execution_environment_id = uuid.uuid4()
            self.logger.info("Initialized EE with ID: %s " % str(self.execution_environment_id))

    def store_ee_info(self):
        """
        Store EE information in file 
        """
        info_file = Configuration.EE_PERSISTENT_INFO_PATH + "infoEE" + self.ee_name
        self.logger.info("Storing EE info to %s" % str(info_file))
        exists = os.path.isfile(info_file)
        if not exists:
            fh = open(info_file, 'w')
            self.logger.info("Storing EE info %s" % str(self.execution_environment_id))
            fh.writelines(str(self.execution_environment_id) + "\n")
            fh.close()
            
    def get_execution_environment_id(self):
        """
        Get execution environment id
        :return: execution environment id
        """
        return self.execution_environment_id
        
    def get_runtime(self):
        """
        @return: Runtime of this Execution Environment 
        """ 
        return self.runtime
    
    def prepareThread(self):
        """ 
        Prepare thread local information. Threads contain information about session, dataset,... and it is also used 
        to obtain proper Runtimes. This function was designed for a multithreading design. 
        IMPORTANT: This function should be called at the beginning of all "public" functions in this module.
        """ 
        setRuntime(self.runtime)
    
    def ds_deploy_metaclasses(self, namespace, classes_map_yamls):
        """Deploy MetaClass containers to the Python Execution Environment.
    
        This function stores in a file all the MetaClass, in addition to (optionally)
        putting them into the cache, according to the ConfigOptions.
    
        :param namespace: The namespace 
        :param classes_map: classes map
        :return: The response (empty string)
        """
        try:
            self.prepareThread()
            for class_name, clazz_yaml in classes_map_yamls.items():
                metaclass = dataclay_yaml_load(clazz_yaml)
                ClassLoader.deploy_metaclass_grpc(
                    namespace, class_name, clazz_yaml, metaclass)
        
                if metaclass.name == "UserType" or metaclass.name == "HashType":
                    logger.warning("Ignoring %s dataClay MetaClass", metaclass.name)
                    logger.debug(metaclass)
                    continue
        
                if metaclass.name == "DataClayPersistentObject" \
                        or metaclass.name == "DataClayObject"\
                        or metaclass.name == "StorageObject":
                    continue
        
                logger.info("Deploying class %s to deployment source path %s",
                             metaclass.name, settings.deploy_path_source)

                try:
                    # ToDo: check whether `lang_codes.LANG_PYTHON` or `'LANG_PYTHON'` is the correct key here
                    import_lines = metaclass.languageDepInfos[LANG_PYTHON].imports
                    imports = "\n".join(import_lines)
                except KeyError:
                    # What is most likely is languageDepInfos not having the Python
                    imports = ""
        
                deploy_class(metaclass.namespace, metaclass.name,
                             metaclass.juxtapose_code(True),
                             imports,
                             settings.deploy_path_source,
                             ds_deploy=True)
                logger.info("Deployment of class %s successful", metaclass.name)
        
            return str()
        except:
            traceback.print_exc()
            return str()
        
    def activate_tracing(self, task_id):
        if not extrae_tracing_is_enabled():
            set_current_available_task_id(task_id)
            initialize_extrae(True)
        
    def deactivate_tracing(self):
        if extrae_tracing_is_enabled():
            finish_tracing(True)

    def get_object_metadatainfo(self, object_id):
        """Get the MetaDataInfo for a certain object.
        :param object_id: The ID of the persistent object
        :return: The MetaDataInfo for the given object.
    
        If we have it available in the cache, return it. Otherwise, call the
        LogicModule for it.
        """
        
        self.prepareThread()
        logger.info("Getting MetaData for object {%s}", object_id)
        return getRuntime().get_metadata(object_id)
    
    def get_local_instance(self, object_id, retry=True):
        self.prepareThread()
        return getRuntime().get_or_new_instance_from_db(object_id, retry)
    
    def get_from_db(self, object_id):
        """Get object directly from StorageLocation (DB).
        
        :param session_id: ID of current session
        :param object_id: ID of object to get
        :return: python object
        """
        self.prepareThread()    
        py_object = getRuntime().get_or_new_instance_from_db(object_id, True)
    
        if py_object is None:
            raise Exception("Object from DB returns None")
    
        return py_object
    
    def internal_exec_impl(self, implementation_name, instance, params):
        """Internal (network-agnostic) execute implementation behaviour.
    
        :param instance: The object in which execution will be performed.
        :param implementation_name: Name of the implementation (may also be some dataClay specific $$get)
        :param params: The parameters (args)
        :return: The return value of the function being executed.
        """
        self.prepareThread()
        
        """
        TODO: use better design for this (dgasull) 
        It is possible that a property is set to None by the GC before we 'execute' it. It should be solve by always 
        checking if loaded before returning value. Check race conditions with GC. 
        """
        if not instance.is_loaded(): 
            getRuntime().load_object_from_db(instance, True)
    
        if implementation_name.startswith(DCLAY_GETTER_PREFIX):
            prop_name = implementation_name[len(DCLAY_GETTER_PREFIX):]
            ret_value = getattr(instance, DCLAY_PROPERTY_PREFIX + prop_name)
            logger.debug("Getter: for property %s returned %r", prop_name, ret_value)
            if not isinstance(ret_value, DataClayObject):
                instance.set_dirty(True)
    
        elif implementation_name.startswith(DCLAY_SETTER_PREFIX):
            prop_name = implementation_name[len(DCLAY_SETTER_PREFIX):]
            logger.debug("Setter: for property %s (value: %r)", prop_name, params[0])
            setattr(instance, DCLAY_PROPERTY_PREFIX + prop_name, params[0])
            ret_value = None
            instance.set_dirty(True)
    
        else:
            logger.debug("Call: %s(*args=%s)", implementation_name, params)
            dataclay_decorated_func = getattr(instance, implementation_name)
            ret_value = dataclay_decorated_func._dclay_entrypoint(instance, *params)
    
        return ret_value
    
    def set_local_session(self, session_id):
        """Set the global `self.thread_local_info` with Session.
    
        :param session_id: The UUID for SessionID.
        :return: None
    
        Set the SessionID
        """
        self.prepareThread()
        self.thread_local_info.session_id = session_id
    
    def store_objects(self, session_id, objects_data_to_store, moving, ids_with_alias):
        """
        @postcondition: Store objects in DB 
        @param session_id: ID of session storing objects 
        @param objects_data_to_store: Objects Data to store 
        @param moving: Indicates if store is done during a move 
        @param ids_with_alias: IDs with alias 
        """
        self.prepareThread()
        
        try:
            self.set_local_session(session_id)

        except Exception as e:
            # TODO: Maybe we need to set local session and dataset in some way
            logger.debug("Trying to set_local_session during store of a federated object"
                        "in a federated dataclay ==> Provided dataclayID instead of sessionID")
            pass

        if ids_with_alias is not None:
            for oid in ids_with_alias: 
                self.runtime.add_alias_reference(oid)
    
        for cur_obj_data in objects_data_to_store: 
            object_id = cur_obj_data[0]
            metadata = cur_obj_data[2]
            obj_bytes = cur_obj_data[3]
            # make persistent - session references
            try:
                getRuntime().add_session_reference(object_id)
            except Exception as e:
                # TODO: See exception in set_local_session
                logger.debug("Trying to add_session_reference during store of a federated object"
                            "in a federated dataclay ==> Provided dataclayID instead of sessionID")
                pass

            bytes_for_db = SerializationLibUtilsSingleton.serialize_for_db(object_id, metadata, obj_bytes, True)
            getRuntime().ready_clients["@STORAGE"].store_to_db(settings.environment_id, object_id, bytes_for_db)    
        
    def register_and_store_pending(self, instance, obj_bytes, sync):
        
        object_id = instance.get_object_id()

        # NOTE! We are doing *two* remote calls, and wishlist => they work as a transaction
        getRuntime().ready_clients["@STORAGE"].store_to_db(settings.environment_id, object_id, obj_bytes)    
        # class_id = instance.get_class_extradata().class_id
        # reg_info = [object_id, class_id, instance.get_owner_session_id(), instance.get_dataset_id()]
        
        dataset_id = None
        dcc_extradata = instance.get_class_extradata()
        reg_info = [object_id, dcc_extradata.class_id, instance.get_owner_session_id(), dataset_id]
        try:
            lm_client = getRuntime().ready_clients["@LM"]
            lm_client.register_object(reg_info, settings.environment_id, None, LANG_PYTHON)
        except:
            # do nothing: alias exception
            pass

        instance.set_pending_to_register(False)

        """
        // Inform MDS about new object !
            final Map<ObjectID, MetaClassID> storedObjs = new ConcurrentHashMap<>();
            storedObjs.put(instance.getObjectID(), instance.getMetaClassID());
    
            final Map<ObjectID, SessionID> objsSessions = new ConcurrentHashMap<>();
            objsSessions.put(instance.getObjectID(), instance.getOwnerSessionIDforVolatiles());
            final RegistrationInfo regInfo = new RegistrationInfo(instance.getObjectID(),
                    instance.getMetaClassID(), instance.getOwnerSessionIDforVolatiles(),
                    instance.getDataSetID());
    
            if (DEBUG_ENABLED) {
                logger.debug("[==RegisterPending==] Going to register " + regInfo + " for instance " + System.identityHashCode(instance));
            }
    
            if (sync) {
                final List<RegistrationInfo> regInfos = new ArrayList<>();
                regInfos.add(regInfo);
                this.runtime.getLogicModuleAPI().registerObjects(regInfos,
                        executionEnvironmentID, null, null, Langs.LANG_JAVA);
            } else {
                this.runtime.getLogicModuleAPI().registerObjectsFromDSGarbageCollector(regInfo,
                        executionEnvironmentID,
                        this.runtime);
            }
        """
        
    def store_in_memory(self, session_id, objects_to_store):
        """ This function will deserialize objects into dataClay memory heap using the same design as for
        volatile parameters. Eventually, dataClay GC will collect them, and then they will be
        registered in LogicModule if needed (if objects were created with alias, they must
        have metadata already).
        :param session_id: ID of session of make persistent call
        :param objects_to_store: objects to store.
        :returns: None
        :type session_id: Session ID
        :type objects_to_store: [num_params, imm_objs, lang_objs, vol_params, pers_params]
        :rtype: None
        """
        self.prepareThread()
        self.set_local_session(session_id)

        # No need to provide params specs or param order since objects are not language types
        return DeserializationLibUtilsSingleton.deserialize_params(objects_to_store, None, None, None, getRuntime())
        
    def make_persistent(self, session_id, objects_to_persist):
        """ This function will deserialize make persistent "parameters" (i.e. object to persist
        and subobjects if needed) into dataClay memory heap using the same design as for
        volatile parameters. Eventually, dataClay GC will collect them, and then they will be
        registered in LogicModule if needed (if objects were created with alias, they must
        have metadata already).
        :param session_id: ID of session of make persistent call
        :param objects_to_persist: objects to store.
        :returns: None
        :type session_id: Session ID
        :type objects_to_persist: [num_params, imm_objs, lang_objs, vol_params, pers_params]
        :rtype: None
        """
        logger.debug("Starting make persistent")
        self.store_in_memory(session_id, objects_to_persist)
        logger.debug("Finished make persistent")

    def federate(self, session_id, objects_to_persist):
        """ This function will deserialize object "parameters" (i.e. object to persist
        and subobjects if needed) into dataClay memory heap using the same design as for
        volatile parameters. This function processes objects recieved from federation calls.
        :param session_id: ID of session of federation call
        :param objects_to_persist: objects to store.
        :returns: None
        :type session_id: Session ID
        :type objects_to_persist: [num_params, imm_objs, lang_objs, vol_params, pers_params]
        """

        logger.debug("Starting federation")
        # No need to provide params specs or param order since objects are not language types
        federated_objs = self.store_in_memory(session_id, objects_to_persist)
        for federated_obj in federated_objs:
            try:
                federated_obj.when_federated()
            except:
                # ignore if method is not implemented
                pass
        
        logger.debug("Finished federation")

    def unfederate(self, session_id, object_ids):
        """ This function is called when objects are unfederated.
        :param session_id: ID of session of federation call
        :param object_ids: List of IDs of the objects to unfederate
        :returns: None
        :type session_id: Session ID
        :type objects_to_persist: Object ID
        """
        self.prepareThread()
        self.set_local_session(session_id)
        logger.debug("Starting unfederation: running when_unfederated")
        for object_id in object_ids:
            instance = self.get_local_instance(object_id, True)
            try:
                instance.when_unfederated() 
            except:
                # ignore if method is not implemented
                pass
        
        logger.debug("Finished unfederation")

    def ds_exec_impl(self, object_id, implementation_id, serialized_params_grpc_msg, session_id):
        """Perform a Remote Execute Implementation.
    
        See Java Implementation for details on parameters and purpose.
        """
        self.prepareThread()
        self.set_local_session(session_id)
        logger.debug("Starting new execution")
        logger.debug("SessionID of current execution: %s", session_id)
        logger.debug("ObjectID of current execution: %s", object_id)
        logger.debug("ImplementationID in which the method belongs: %s", implementation_id)
    
        instance = self.get_local_instance(object_id, True)
    
        metaclass_container = instance.get_class_extradata().metaclass_container
        operation = metaclass_container.get_operation(implementation_id)
        logger.debug("DESERIALIZING PARAMETERS")
    
        num_params = serialized_params_grpc_msg[0]
        params = [] 
        if num_params > 0:
            params = DeserializationLibUtilsSingleton.deserialize_params(serialized_params_grpc_msg, None,
                                        operation.params,
                                        operation.paramsOrder, getRuntime())
        logger.debug("STARTING EXECUTION")
    
        ret_value = self.internal_exec_impl(operation.name,
                                       instance,
                                       params)
        
        logger.debug("SERIALIZING RESULT ")
        if ret_value is None:
            logger.debug(" -> Returning None")
            return None
        
        logger.debug(" -> Serializing %s (type: %s)", ret_value, operation.returnType)
        return SerializationLibUtilsSingleton.serialize_params_or_return({0: ret_value},
                                          None,
                                          {"0": operation.returnType},
                                          ["0"],
                                          None,
                                          getRuntime(),
                                          True)  # No volatiles inside EEs
    
    def new_persistent_instance(self, payload):
        """Create, make persistent and return an instance for a certain class."""
    
        raise NotImplementedError("NewPersistentInstance RPC is not yet ready (@ Python ExecutionEnvironment)")
    
    def new_replica(self, session_id, object_id, recursive):
        """Creates a new replica of the object with ID provided in the backend specified.
    
    	:param session_id: ID of session
    	:param object_id: ID of the object
    	:param recursive: Indicates if all sub-objects must be replicated as well.
    	:return: Set of IDs of replicated objects
    	"""
        logger.debug("[==Replica==] New replica for %s", object_id)
        self.prepareThread()
        
        object_ids = set()
        object_ids.add(object_id)
        serialized_objs = self.get_objects(session_id, object_ids, recursive, False)
    
        # Adds associated oid found in metadata in object_ids
        for obj_found in serialized_objs:
            for k in obj_found[2][0]:
                oid = obj_found[2][0][k]
                if oid not in object_ids:
                    logger.verbose("[==Replica==] Associated OID %s found in serialized_objects and not in object_ids", oid)
                    object_ids.add(oid)
                if not recursive:
                    break
    
        logger.debug("[==Replica==] Serialized_objs at the end are %s", serialized_objs)
    
        objects_list = self._check_and_prepare(serialized_objs)
    
        logger.debug("[==Replica==] Object list to store is %s", objects_list)
    
        for obj_id in object_ids:
            for obj in objects_list:
                obj_bytes = obj[3]
                if obj[0] == obj_id:                
                    metadata = obj[2]
                    bytes_for_db = SerializationLibUtilsSingleton.serialize_for_db(obj_id, metadata, obj_bytes, False)
                    getRuntime().ready_clients["@STORAGE"].store_to_db(settings.environment_id, obj_id, bytes_for_db)    
    
        return object_ids
    
    def get_copy_of_object(self, session_id, object_id, recursive):
        """Returns a non-persistent copy of the object with ID provided
    
        :param session_id: ID of session
        :param object_id: ID of the object
        :return: the generated non-persistent objects
        """
        logger.debug("[==Get==] Get copy of %s ", object_id)
        self.prepareThread()
    
        # Get the data service of one of the backends that contains the original object.
        object_ids = set()
        object_ids.add(object_id)
    
        serialized_objs = self.get_objects(session_id, object_ids, recursive, False)
    
        # Prepare OIDs
        logger.debug("[==Get==] Serialized objects obtained to create a copy of %s are %s", object_id, serialized_objs)
        original_to_version = dict()
    
        # Store version in this backend (if already stored, just skip it)
        for obj in serialized_objs:
            orig_obj_id = obj[0]
            version_obj_id = uuid.uuid4()
            original_to_version[orig_obj_id] = version_obj_id
    
        serialized_objs = [self._modify_metadata_oids(obj, original_to_version) for obj in serialized_objs]
        serialized_objs = [self._modify_oid(obj, original_to_version) for obj in serialized_objs]
            
        logger.debug("[==Get==] Serialized Objects after OIDs regeneration are %s", serialized_objs)
            
        i = 0   
        imm_objs = dict()
        lang_objs = dict()
        vol_params = dict()
        pers_params = dict()
        for obj in serialized_objs:
            vol_params[i] = obj
            i = i + 1
    
        serialized_result = [i, imm_objs, lang_objs, vol_params, pers_params]
        
        return serialized_result
        
    def update_object(self, session_id, into_object_id, from_object):
        """Updates an object with ID provided with contents from another object
        :param session_id: ID of session
        :param into_object_id: ID of the object to be updated
        :param from_object: object with contents to be used
        """
        self.prepareThread()
        self.set_local_session(session_id)
        logger.debug("[==PutObject==] Updating object %s", into_object_id)
        object_into = getRuntime().get_or_new_instance_from_db(into_object_id, False)
        object_from = DeserializationLibUtilsSingleton.deserialize_params_or_return(from_object, None, None, None, getRuntime())[0]
        object_into.set_all(object_from)
        logger.debug("[==PutObject==] Updated object %s from object %s", into_object_id, object_from.get_object_id())
        
    def get_objects(self, session_id, object_ids, recursive, moving):
        """Get the serialized objects with id provided
    	:param session_id: ID of session
    	:param object_ids: IDs of the objects to get
    	:param recursive: Indicates if, per each object to get, also obtain its associated objects.
    	:param moving: Indicates we are getting object for a move
    	:return: List of serialized objects with ids provided
        """
        logger.debug("[==Get==] Getting objects %s", object_ids)
        self.prepareThread()
    
        result = list()
        self.thread_local_info.session_id = session_id
        pending_oids_and_hint = list()
        obtained_objs = dict()
        objects_in_other_backend = list()
    
        for oid in object_ids:
            if recursive:
                # Add object to pending
                pending_oids_and_hint.append([oid, None])
                while pending_oids_and_hint:
                    current_oid_and_hint = pending_oids_and_hint.pop()
                    current_oid = current_oid_and_hint[0]
                    current_hint = current_oid_and_hint[1]
                    if current_oid in obtained_objs:
                        # Already Read
                        logger.verbose("[==Get==] Object %s already read", current_oid)
                        continue
    
                    else:
                        try:
                            logger.verbose("[==Get==] Trying to get local instance for object %s", current_oid)    
                            obj_with_data = self.get_object_internal(current_oid, moving)
                            result.append(obj_with_data)
                            obtained_objs[current_oid] = current_hint
                            # Get associated objects and add them to pendings
                            for k in obj_with_data[2][0]:
                                oid_found = obj_with_data[2][0][k]
                                hint_found = obj_with_data[2][2][k]
                                if oid_found != current_oid and oid_found not in obtained_objs:
                                    pending_oids_and_hint.append([oid_found, hint_found])
    
                        except: 
                            logger.debug("[==Get==] Object is in other backend")
                            # Get in other backend
                            objects_in_other_backend.append([current_oid, current_hint])
            else:
                try:
                    result.append(self.get_object_internal(oid, moving))
                except:
                    logger.debug("[==Get==] Object is in other backend")
                    # Get in other backend
                    objects_in_other_backend.append([oid, None])
    
        obj_with_data_in_other_backends = self.get_objects_in_other_backends(session_id, objects_in_other_backend,
                                                                        recursive, moving)
    
        logger.verbose("[==Get==] Object with data return length: %d", len(obj_with_data_in_other_backends))
        logger.trace("[==Get==] Object with data in other backends content: %s", obj_with_data_in_other_backends)
        for obj_in_oth_back in obj_with_data_in_other_backends:
            logger.trace("[==Get==] Append %s to the result", obj_in_oth_back)
            result.append(obj_in_oth_back)
    
        checked_result = self._check_and_prepare(result)
    
        return checked_result
    
    def get_object_internal(self, oid, moving):
        """Get object internal function
    	:param oid: ID of the object ot get
    	:param moving: Indicates we are getting object for a move
    	:return: Object with data
    	:type oid: ObjectID 
    	:type moving: boolean
    	:rtype: Object with data
        """
        # Serialize the object
        logger.verbose("[==GetInternal==] Trying to get local instance for object %s", oid)
        self.prepareThread()
        
        # ToDo: Manage better this try/catch
        getRuntime().lock(oid)  # Race condition with gc: make sure GC does not CLEAN the object while retrieving/serializing it!
        try:
            current_obj = self.get_local_instance(oid, False)
        
            if moving:
                # TODO: Remove hint for moving in order to avoid hints to be also moved.
                pass

            if current_obj.is_pending_to_register():
                # FORCE VOLATILE TO BE REGISTERED
                obj_bytes = SerializationLibUtilsSingleton.serialize_for_db_gc(current_obj, False, None)
                # Register object pending to register now in order to be consistent with any process (metadatas...)
                self.register_and_store_pending(current_obj, obj_bytes, True)
            pending_objs = list()

            # Hint for object located here is here.
            hint = self.get_runtime().get_hint()
    
            # Add object to result and obtained_objs for return and recursive
            return SerializationLibUtilsSingleton.serialize_dcobj_with_data(current_obj, pending_objs,
                                             False, hint, getRuntime(), False)
        finally:
            getRuntime().unlock(oid)          
    
    def get_objects_in_other_backends(self, session_id, objects_in_other_backend, recursive, moving):
        """Get object in another backend. This function is called from DbHandler in a recursive get.
    
    	:param session_id: ID of session
    	:param objects_in_other_backend: List of metadata of objects to read. It is useful to avoid multiple trips.
    	:param recursive: Indicates is recursive
    	:param moving: Indicates if moving
    	:return: ID of objects and for each object, its bytes.
        """
        self.prepareThread()
        result = list()
    
        # Prepare to unify calls (only one call for DS)
        objects_per_backend = dict()
    
        for curr_oid_and_hint in objects_in_other_backend:
            curr_oid = curr_oid_and_hint[0]
            curr_hint = curr_oid_and_hint[1]
            
            logger.debug("[==GetObjectsInOtherBackend==] Looking for metadata of %s", curr_oid)
            
            metadata = self.get_object_metadatainfo(curr_oid)
            logger.info("metadata info are %s", metadata)

            if metadata is None: 
                if curr_hint is not None: 
                    location = curr_hint 
                else: 
                    raise Exception("Object %s not registered" % curr_oid)
            else:
                locations = metadata.locations
                # TODO: Check why always obtain from the first location
                location = next(iter(locations.keys()))
            try:
                objects_in_backend = objects_per_backend[location]
            except KeyError:
                objects_in_backend = set()
                objects_per_backend[location] = objects_in_backend
            objects_in_backend.add(curr_oid)
    
        # Now Call
        for backend_id, objects_to_get in objects_per_backend.items():
    
            logger.debug("[==GetObjectsInOtherBackend==] Get from other location, objects: %s", objects_to_get)
            backend = getRuntime().ready_clients["@LM"].get_executionenvironment_for_ds(backend_id)
    
            try:
                client_backend = getRuntime().ready_clients[backend_id]
            except KeyError:
                logger.verbose("[==GetObjectsInOtherBackend==] Not found Client to ExecutionEnvironment {%s}!"
                               " Starting it at %s:%d", backend_id, backend.hostname, backend.port)
    
                client_backend = EEClient(backend.hostname, backend.port)
                getRuntime().ready_clients[backend_id] = client_backend
    
            cur_result = client_backend.ds_get_objects(session_id, objects_to_get, recursive, moving)
    
            logger.verbose("[==GetObjectsInOtherBackend==] call return length: %d", len(cur_result))
            logger.trace("[==GetObjectsInOtherBackend==] call return content: %s", cur_result)
    
            for res in cur_result:
                result.append(res)
    
        return result
    
    def get_referenced_objects_ids(self, session_id, object_ids):
        """Get ids of objects referenced by objects with IDs provided
        :param session_id: ID of session
        :param object_ids: IDs of the objects that can reference 
        :return: List of object ids referenced by objects with IDs provided
        :type session_id: Session ID
        :type object_ids: set
        :rtype: set of object ids
        """
        logger.debug("[==Get references==] Getting references of objects %s", object_ids)
        self.prepareThread()
        
        result = set()
        self.thread_local_info.session_id = session_id
        pending_oids_and_hint = list()
        obtained_objs = dict()
        objects_in_other_backend = list()
    
        for oid in object_ids:
            # Add object to pending
            pending_oids_and_hint.append([oid, None])
            while pending_oids_and_hint:
                current_oid_and_hint = pending_oids_and_hint.pop()
                current_oid = current_oid_and_hint[0]
                current_hint = current_oid_and_hint[1]
                if current_oid in obtained_objs:
                    # Already Read
                    logger.verbose("[==Get==] Object %s already read", current_oid)
                    continue
    
                else:
                    try:
                        logger.verbose("[==Get==] Trying to get local instance for object %s", current_oid)    
                        obj_with_data = self.get_object_internal(current_oid, False)
                        obtained_objs[current_oid] = current_hint
                        # Get associated objects and add them to pendings
                        for k in obj_with_data[2][0]:
                            oid_found = obj_with_data[2][0][k]
                            hint_found = obj_with_data[2][2][k]
                            if oid_found != current_oid and oid_found not in obtained_objs:
                                pending_oids_and_hint.append([oid_found, hint_found])
                                result.add(oid_found)
    
                    except Exception: 
                        logger.debug("[==Get==] Object is in other backend")
                        # Get in other backend
                        objects_in_other_backend.append([current_oid, current_hint])
    
        oids_in_other_ee = self.get_objects_ids_in_other_backends(session_id, objects_in_other_backend)
        for other_ee_oid in oids_in_other_ee:
            result.add(other_ee_oid)
            
        logger.debug("[==Get references==] Result %s", str(result))
   
        return result
    
    def get_objects_ids_in_other_backends(self, session_id, objects_in_other_backend):
        """Get IDs of objects referenced by provided object ids in another backend
        :param session_id: ID of session
        :param objects_in_other_backend: List of metadata of objects to read. It is useful to avoid multiple trips.
        :return: ID of objectss in another backend
        :type session_id: Session ID
        :type object_ids: set
        :rtype: set of object ids referenced by provided object ids in another backend
        """ 
        self.prepareThread()
        result = list()
    
        # Prepare to unify calls (only one call for DS)
        objects_per_backend = dict()
    
        for curr_oid_and_hint in objects_in_other_backend:
            curr_oid = curr_oid_and_hint[0]
            curr_hint = curr_oid_and_hint[1]
            logger.debug("[==GetOIDsObjectsInOtherBackend==] Looking for metadata of %s", curr_oid)
            metadata = self.get_object_metadatainfo(curr_oid)
            logger.info("metadata info are %s", metadata)
            if metadata is None: 
                if curr_hint is not None: 
                    location = curr_hint 
                else: 
                    raise Exception("Object %s not registered" % curr_oid)
            else:
                locations = metadata.locations
                # TODO: Check why always obtain from the first location
                location = next(iter(locations.keys()))
    
            try:
                objects_in_backend = objects_per_backend[location]
            except KeyError:
                objects_in_backend = set()
                objects_per_backend[location] = objects_in_backend
            objects_in_backend.add(curr_oid)
    
        # Now Call
        for backend_id, objects_to_get in objects_per_backend.items():
    
            logger.debug("[==GetOIDsObjectsInOtherBackend==] Get from other location, objects: %s", objects_to_get)
            backend = getRuntime().ready_clients["@LM"].get_executionenvironment_for_ds(backend_id)
    
            try:
                client_backend = getRuntime().ready_clients[backend_id]
            except KeyError:
                logger.verbose("[==GetOIDsObjectsInOtherBackend==] Not found Client to ExecutionEnvironment {%s}!"
                               " Starting it at %s:%d", backend_id, backend.hostname, backend.port)
    
                client_backend = EEClient(backend.hostname, backend.port)
                getRuntime().ready_clients[backend_id] = client_backend
    
            cur_result = client_backend.get_referenced_objects_ids(session_id, objects_to_get)
    
            logger.verbose("[==GetOIDsObjectsInOtherBackend==] call return length: %d", len(cur_result))
            logger.trace("[==GetOIDsObjectsInOtherBackend==] call return content: %s", cur_result)
    
            for res in cur_result:
                result.append(res)
    
        return result
    
    def new_version(self, session_id, object_id, metadata_info):
        """Creates a new version of the object with ID provided in the backend specified.
    
    	:param session_id: ID of session
    	:param object_id: ID of the object
    	:param metadata_info: Metadata of the object, including the backends where the root object to be versioned is located
    	:return: The OID of the version root and the mapping from version OID to original OID for each versioned object
        """
        self.prepareThread()
        logger.debug("[==Version==] New version for %s ", object_id)
    
        # Get the data service of one of the backends that contains the original object.
        object_ids = set()
        object_ids.add(object_id)
    
        serialized_objs = self.get_objects(session_id, object_ids, True, False)
    
        # Prepare OIDs
        logger.debug("[==Version==] Serialized objects obtained to create version for %s are %s", object_id, serialized_objs)
        version_to_original = dict()
        original_to_version = dict()
        versions_hints = dict()
    
        # Store version in this backend (if already stored, just skip it)
        for obj in serialized_objs:
            orig_obj_id = obj[0]
            version_obj_id = uuid.uuid4()
            version_to_original[version_obj_id] = orig_obj_id
            original_to_version[orig_obj_id] = version_obj_id
            # ToDo: Manage hints for versions_hints dict
            # versions_hints[version_obj_id] = hint
    
        # ToDo: Add also versions_hints to modify_metadata_oids
        serialized_objs = [self._modify_metadata_oids(obj, original_to_version) for obj in serialized_objs]
        serialized_objs = [self._modify_oid(obj, original_to_version) for obj in serialized_objs]
    
        logger.debug("[==Version==] Serialized Objects after modification are %s", serialized_objs)
    
        # Store versions
        objs_to_store = self._check_and_prepare(serialized_objs)
    
        for obj in objs_to_store:
            obj_id = obj[0]
            metadata = obj[2]
            obj_bytes = obj[3]
            logger.info("obj_id is %s, obj_data are %s", obj_id, obj_bytes)
            
            bytes_for_db = SerializationLibUtilsSingleton.serialize_for_db(obj_id, metadata, obj_bytes, False)
            
            getRuntime().ready_clients["@STORAGE"].store_to_db(settings.environment_id, obj_id, bytes_for_db)
            
        # Modify metadata_info
        version_id = original_to_version[object_id]
        environments = dict()
        environments[settings.environment_id] = getRuntime().ready_clients["@LM"].get_executionenvironment_for_ds(settings.environment_id)
    
        logger.debug("[==Version==] Modifying metadataInfo: %s", metadata_info)
        version_md = metadata_info
        version_md.locations = environments
        logger.debug("[==Version==] Added metadata info to MetaData Cache: %s : %s", version_id, version_md)
        getRuntime().metadata_cache[version_id] = version_md
        logger.debug("[==Version==] Version finished for object %s , newVersion oid is: %s", object_id, version_id)
    
        return version_id, version_to_original
    
    def consolidate_version(self, session_id, version):
        """Consolidates all the objects in versionInfo, being the current data service the one containing all the versioned
    	   objects. For each versioned object, its OID is set to the original one according to the mapping in versionInfo,
    	   and the consolidated object is stored in the same locations as the original one (before versioning). The versions
    	   are deleted.
    
    	:param session_id:ID of session
    	:param version: Info of the version
        """
        self.prepareThread()
        # Consolidate in this backend - the complete version is here
        version_to_original = version.versionsMapping
        original_hints = dict()

        for version_oid, original_oid in version_to_original.items():
            original_md = version.originalMD[original_oid]
            original_hints[original_oid] = list(original_md.locations.keys())[0]

        logger.debug("[==Consolidate==] Consolidating version %s to original %s", version.versionOID, version_to_original.get(version.versionOID))
    
        version_object_ids = set()

        # Get bytes of all version objects
        for k in list(version_to_original.keys()):
            version_object_ids.add(k)

        dirty_version_bytes = self.get_objects(session_id, version_object_ids, True, False)
        logger.debug("[==Consolidate==] Version objs obtained are %s", dirty_version_bytes)
    
        # Update original objects
        # ToDo: Change also versions_hints in modify_metadata_oids
        version_bytes = list()
    
        for vers_byte in dirty_version_bytes:
            # Change the stream position to 0
            vers_byte[3].seek(0)
            # Modify metadata and oid with the versions one
            modified_metadata = self._modify_metadata_oids(vers_byte, version_to_original)
            modified_oid = self._modify_oid(modified_metadata, version_to_original)
            version_bytes.append(modified_oid)
    
        logger.trace("[==Consolidate==] Version objs modified are %s", version_bytes)
    
        dest_loc = None
    
        try:
            self.thread_local_info.session_id = session_id
    
            # Update original objects (here and in other DSs - replicas)
            orig_oid = version_to_original[version.versionOID]
            md_info = version.originalMD[orig_oid]
            locs = md_info.locations
            for loc_id in locs:
                dest_loc = locs[loc_id]
                if loc_id == settings.environment_id:
                    logger.verbose("[==Consolidate==] Upsert Objects in this DS")
                    self.upsert_objects(session_id, version_bytes)
                else:
                    try:
                        st_client = getRuntime().ready_clients[loc_id]
                    except KeyError:
                        logger.verbose("[==Consolidate==] Not found Client to ExecutionEnvironment {%s}!"
                                       " Starting it at %s:%d", loc_id, dest_loc.hostname, dest_loc.port)
    
                        st_client = EEClient(dest_loc.hostname, dest_loc.port)
                        getRuntime().ready_clients[loc_id] = st_client
    
                    logger.debug("[==Consolidate==] Going to other DS to upsert %s", version_to_original[version.versionOID])
                    st_client.ds_upsert_objects(session_id, version_bytes)
    
                # Delete versions here
                # TODO: G.C. should do it
                # commonruntime.ready_clients["@STORAGE"].ds_remove_objects(session_id, version_object_ids, True, False, dest_loc)
    
        except Exception as e:
            traceback.print_exc()
            logger.error("Exception during Consolidate Version")
            raise e
        
        logger.debug("[==Consolidate==] Consolidate ended")
    
    def _check_and_prepare(self, serialized_objs):
        """ Check if serialized_obj are in the right format and prepare the objects_list to send to store_objects """
        objects_list = list()
    
        for obj in serialized_objs:
            logger.trace("[==CheckAndPrepare==] Obj in Serialized objs content: %s", obj)
    
            # Since the ds_store_objects is serializing again we deserialize the data before sending it
            # ToDo: Correct this
            if not isinstance(obj[3], BytesIO):
                logger.verbose("Type for (obj[3]): %s", type(obj))
                logger.trace("Bytes (obj[3]) serialized in wrong way for %s", obj)
                serialized_obj = BytesIO(obj[3])
            else:
                serialized_obj = obj[3]
            dcobj = obj[0], obj[1], obj[2], serialized_obj
            objects_list.append(dcobj)
    
        return objects_list
    
    def _modify_metadata_oids(self, obj, original_to_version):
        """ Modify the version's metadata in serialized_objs with original OID"""
        self.prepareThread()
        logger.debug("[==ModifyMetadataOids==] Modify serialized object %r", obj)
        logger.debug("[==ModifyMetadataOids==] Version OIDs Map: %s", original_to_version)

        for tag, oid in obj[2][0].items():
            try:
                obj[2][0][tag] = original_to_version[oid]
            except KeyError:
                logger.debug("[==ModifyMetadataOids==] oid %s is not mapped => object added in the version", oid)
                # obj[2][0][tag] = oid
                pass

        logger.debug("[==ModifyMetadataOids==] Object with modified metadata is %r", obj)

        return obj
    
    def _modify_oid(self, obj, original_to_version):
        """ Modify the version's OID in serialized_objs with the original OID"""
        try:
            new_obj = original_to_version[obj[0]], obj[1], obj[2], obj[3]
        except KeyError:
            # OID in object are already changed
            new_obj = obj
        return new_obj

    def upsert_objects(self, session_id, object_ids_and_bytes):
        """Updates objects or insert if they do not exist with the values in objectBytes.
        NOTE: This function is recursive, it is going to other DSs if needed.
        :param session_id: ID of session needed.
    	:param object_ids_and_bytes: Map of objects to update.
    	"""
        self.prepareThread()
        self.thread_local_info.session_id = session_id

        try:
            objects_in_other_backends = list()
    
            # To check for replicas
            for cur_entry in object_ids_and_bytes:
                # ToDo: G.C. stuffs
                object_id = cur_entry[0]
                logger.debug("[==Upsert==] Updated or inserted object %s", object_id)
                try:
                    # Update bytes at memory object
                    logger.debug("[==Upsert==] Getting/Creating instance from upsert with id %s", object_id)
                    instance = getRuntime().get_or_new_instance_from_db(object_id, False)
                    DeserializationLibUtilsSingleton.deserialize_object_with_data(cur_entry, instance, None, getRuntime(), getRuntime().get_session_id(), True)
                    
                    instance.set_dirty(True)
                    
                except Exception:
                    # Get in other backend
                    objects_in_other_backends.append(cur_entry)
    
            self.upsert_objects_in_other_backend(session_id, objects_in_other_backends)
    
        except Exception as e:
            traceback.print_exc()
            logger.error("Exception during Upsert Objects")
            raise e
    
    def upsert_objects_in_other_backend(self, session_id, objects_in_other_backends):
        """Update object in another backend.
    
    	:param session_id: ID of session
    	:param objects_in_other_backends: List of metadata of objects to update and its bytes. It is useful to avoid multiple trips.
    	:return: ID of objects and for each object, its bytes.
        """
        self.prepareThread()
        # Prepare to unify calls (only one call for DS)
        objects_per_backend = dict()
        for curr_obj_with_ids in objects_in_other_backends:
            
            curr_oid = curr_obj_with_ids[0]
            locations = self.get_object_metadatainfo(curr_oid).locations
            location = next(iter(locations.keys()))
            # Update object at first location (NOT UPDATING REPLICAS!!!)
            try:
                objects_in_backend = objects_per_backend[location]
            except KeyError:
                objects_in_backend = list()
                objects_per_backend[location] = objects_in_backend
                
            objects_in_backend.append(curr_obj_with_ids)
        # Now Call
        for backend_id, objects_to_update in objects_per_backend.items():
    
            backend = getRuntime().ready_clients["@LM"].get_executionenvironment_for_ds(backend_id)
    
            try:
                client_backend = getRuntime().ready_clients[backend_id]
            except KeyError:
                logger.verbose("[==GetObjectsInOtherBackend==] Not found Client to ExecutionEnvironment {%s}!"
                               " Starting it at %s:%d", backend_id, backend.hostname, backend.port)
    
                client_backend = EEClient(backend.hostname, backend.port)
                getRuntime().ready_clients[backend_id] = client_backend
    
            client_backend.ds_upsert_objects(session_id, objects_to_update)

    def move_objects(self, session_id, object_id, dest_backend_id, recursive):
        """This operation removes the objects with IDs provided NOTE:
         This function is recursive, it is going to other DSs if needed.
    
    	:param session_id: ID of session.
    	:param object_id: ID of the object to move.
        :param dest_backend_id: ID of the backend where to move.
        :param recursive: Indicates if all sub-objects (in this location or others) must be moved as well.
    	:return: Set of moved objects.
        """
        update_metadata_of = set()

        try:
            logger.debug("[==MoveObjects==] Moving object %s to storage location: %s", object_id, dest_backend_id)
            object_ids = set()
            object_ids.add(object_id)

            # TODO: Object being used by session (any oid in the method header) G.C.

            serialized_objs = self.get_objects(session_id, object_ids, recursive, True)
            objects_to_remove = set()
            objects_to_move = list()

            for obj_found in serialized_objs:
                logger.debug("[==MoveObjects==] Looking for metadata of %s", obj_found[0])
                metadata = self.get_object_metadatainfo(obj_found[0])
                obj_location = list(metadata.locations.keys())[0]

                if obj_location == dest_backend_id:
                    logger.debug("[==MoveObjects==] Ignoring move of object %s since it is already where it should be."
                    " ObjLoc = %s and DestLoc = %s" , obj_found[0], obj_location, dest_backend_id)
					
					# object already in dest
                    pass
                else:
                    if settings.storage_id == dest_backend_id:
                        # THE DESTINATION IS HERE
                        if obj_location != settings.storage_id:
                            logger.debug("[==MoveObjects==] Moving object  %s since dest.location is different to src.location and object is not in dest.location."
										 " ObjLoc = %s and DestLoc = %s", obj_found[0], obj_location, dest_backend_id)
                            objects_to_move.append(obj_found)
                            objects_to_remove.add(obj_found[0])
                            update_metadata_of.add(obj_found[0])
                        else:
                            logger.debug("[==MoveObjects==] Ignoring move of object %s since it is already where it should be"
										 " ObjLoc = %s and DestLoc = %s", obj_found[0], obj_location, dest_backend_id)
                    else:
                        logger.debug("[==MoveObjects==] Moving object %s since dest.location is different to src.location and object is not in dest.location "
                                        " ObjLoc = %s and DestLoc = %s", obj_found[0], obj_location, dest_backend_id)
                        # THE DESTINATION IS ANOTHER NODE: move.
                        objects_to_move.append(obj_found)
                        objects_to_remove.add(obj_found[0])
                        update_metadata_of.add(obj_found[0])

            logger.debug("[==MoveObjects==] Finally moving OBJECTS: %s", objects_to_remove)

            try:
                sl_client = getRuntime().ready_clients[dest_backend_id]
            except KeyError:
                st_loc = getRuntime().get_execution_environments_info()[dest_backend_id] 
                self.logger.debug("Not found in cache ExecutionEnvironment {%s}! Starting it at %s:%d",
                               dest_backend_id, st_loc.hostname, st_loc.port)
                sl_client = EEClient(st_loc.hostname, st_loc.port)
                getRuntime().ready_clients[dest_backend_id] = sl_client

            sl_client.ds_store_objects(session_id, objects_to_move, True, None)

            # TODO: lock any execution in remove before storing objects in remote dataservice so anyone can modify it.
			# Remove after store in order to avoid wrong executions during the movement :)
			# Remove all objects in all source locations different to dest. location
            # TODO: Check that remove is not necessary (G.C. Should do it?)
            # getRuntime().ready_clients["@STORAGE"].ds_remove_objects(session_id, object_ids, recursive, True, dest_backend_id)

            for oid in objects_to_remove:
                if oid in getRuntime().metadata_cache:
                    del getRuntime().metadata_cache[oid]
            logger.debug("[==MoveObjects==] Move finalized ")

        except Exception as e:
            logger.error("[==MoveObjects==] Exception %s", e.args)

        return update_metadata_of
    
    def update_refs(self, ref_counting):
        """ forward to SL """ 
        self.prepareThread()
        getRuntime().ready_clients["@STORAGE"].update_refs(ref_counting)    

    def get_retained_references(self):
        return self.runtime.get_retained_references()
    
    def close_session_in_ee(self, session_id):
        self.runtime.close_session_in_ee(session_id)
        
    def exists(self, object_id):
        
        # object might be in heap but as a "proxy" 
        # since this function is used from SL after checking if the object is in database, 
        # we return false if the object is not loaded so the combination of SL exists and EE exists
        # can tell if the object actually exists
        # summary: the object only exist in EE if it is loaded. 
        
        in_heap = self.runtime.exists(object_id)
        if in_heap: 
            obj = self.runtime.get_from_heap(object_id)
            return obj.is_loaded()
        else:
            return False

    def get_federated_objects(self, ext_dataclay_id, object_ids):
        
        self.prepareThread()
        logger.debug("[==GetFederatedObjects==] Getting objects %s", object_ids)
        result = []
        try:
            for object_id in object_ids:
                if not getRuntime().ready_clients["@LM"].check_object_is_federated_with_dataclay_instance(
                    object_id, ext_dataclay_id):
                    
                    logger.debug("[==GetFederatedObjects==] Object %s not federated with ext.dataclay %s", object_id, ext_dataclay_id)

                    return None
            
            for object_id in object_ids:
                obj_with_data = self.get_object_internal(object_id, False)
                result.append(obj_with_data)
        
        except Exception as e:
            traceback.print_exc()
            logger.error("[==GetFederatedObjects==] Exception %s", e)
        
        return result

    def get_traces(self):
        logger.debug("Merging...")
        return get_traces()
    
    ################## EXTRAE IGNORED FUNCTIONS ###########################
    deactivate_tracing.do_not_trace = True
    activate_tracing.do_not_trace = True
