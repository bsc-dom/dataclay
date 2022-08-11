""" Class description goes here. """

import logging
import os
import time
import traceback
import uuid
from ctypes import c_void_p
from io import BytesIO

import lru
from dataclay_common.managers.object_manager import ObjectMetadata
from dataclay_common.protos.common_messages_pb2 import LANG_PYTHON

from dataclay.commonruntime.ExecutionEnvironmentRuntime import ExecutionEnvironmentRuntime
from dataclay.commonruntime.Runtime import get_runtime, set_runtime
from dataclay.commonruntime.Settings import settings
from dataclay.communication.grpc.clients.ExecutionEnvGrpcClient import EEClient
from dataclay.communication.grpc.clients.LogicModuleGrpcClient import LMClient
from dataclay.DataClayObject import DataClayObject
from dataclay.DataClayObjProperties import (DCLAY_GETTER_PREFIX, DCLAY_PROPERTY_PREFIX,
                                            DCLAY_SETTER_PREFIX)
from dataclay.exceptions.exceptions import DataClayException
from dataclay.paraver import (extrae_tracing_is_enabled, finish_tracing, get_traces,
                              initialize_extrae, set_current_available_task_id)
from dataclay.serialization.lib.DeserializationLibUtils import DeserializationLibUtilsSingleton
from dataclay.serialization.lib.ObjectWithDataParamOrReturn import ObjectWithDataParamOrReturn
from dataclay.serialization.lib.SerializationLibUtils import SerializationLibUtilsSingleton
from dataclay.serialization.lib.SerializedParametersOrReturn import SerializedParametersOrReturn
from dataclay.util import Configuration
from dataclay.util.classloaders import ClassLoader
from dataclay.util.FileUtils import deploy_class
from dataclay.util.YamlParser import dataclay_yaml_load

__author__ = "Alex Barcelo <alex.barcelo@bsc.es>"
__copyright__ = "2015 Barcelona Supercomputing Center (BSC-CNS)"

from dataclay.util.management.metadataservice.RegistrationInfo import RegistrationInfo

logger = logging.getLogger(__name__)


class ExecutionEnvironment(object):
    def __init__(self, theee_name, theee_port):
        self.runtime = ExecutionEnvironmentRuntime(self)
        set_runtime(self.runtime)

        self.ee_name = theee_name
        # Note that the port is (atm) exclusively for unique identification of an EE
        # (given that the name is shared between all EE that share a SL, which happens in HPC deployments)
        self.ee_port = theee_port

        # Initialize runtime
        self.runtime.initialize_runtime()
        # TODO: de-hardcode this value
        self.cached_sessioninfo = lru.LRU(50)
        self.logger = logging.getLogger(__name__)

        self.init_ee_info()
        # store ee info
        self.store_ee_info()

    @property
    def info_file(self):
        # Note that we are dynamically evaluating it just in case things happen
        # (e.g. the Configuration changes during runtime)
        # I may be acting overzealously
        return f"{Configuration.STORAGE_METADATA_PATH}/python_ee_{self.ee_name}%{self.ee_port}.info"

    def init_ee_info(self):
        """
        Initialize EE information (ID). Try to find information in stored files first, otherwise create EE ID.
        """
        info_file = self.info_file
        exists = os.path.isfile(info_file)
        self.logger.info("Reading EE info from %s" % str(info_file))
        if exists:
            fh = open(info_file, "r+")
            line = fh.readline()
            self.logger.info("READ LINE %s" % str(line))
            self.execution_environment_id = uuid.UUID(line.strip())
            self.logger.info(
                "Initialized EE from file with ID: %s" % str(self.execution_environment_id)
            )
            fh.close()

        else:
            self.execution_environment_id = uuid.uuid4()
            self.logger.info("Initialized EE with ID: %s " % str(self.execution_environment_id))

    def store_ee_info(self):
        """
        Store EE information in file
        """
        info_file = self.info_file
        self.logger.info("Storing EE info to %s" % str(info_file))
        exists = os.path.isfile(info_file)
        if not exists:
            fh = open(info_file, "w")
            self.logger.info("Storing EE info %s" % str(self.execution_environment_id))
            fh.writelines(str(self.execution_environment_id) + "\n")
            fh.close()

    def notify_execution_environment_shutdown(self):
        """
        Notify LM current node left
        :return: None
        """
        lm_client = get_runtime().ready_clients["@LM"]
        lm_client.notify_execution_environment_shutdown(self.execution_environment_id)

    def get_execution_environment_id(self):
        """
        Get execution environment id
        :return: execution environment id
        """
        return self.execution_environment_id

    def prepareThread(self):
        """
        Prepare thread local information. Threads contain information about session, dataset,... and it is also used
        to obtain proper Runtimes. This function was designed for a multithreading design.
        IMPORTANT: This function should be called at the beginning of all "public" functions in this module.
        """
        # set_runtime(self.runtime)

    def ds_deploy_metaclasses(self, namespace, classes_map_yamls):
        """Deploy MetaClass containers to the Python Execution Environment.

        This function stores in a file all the MetaClass, in addition to (optionally)
        putting them into the cache, according to the ConfigOptions.

        :param namespace: The namespace
        :param classes_map: classes map
        :return: The response (empty string)
        """
        try:
            for class_name, clazz_yaml in classes_map_yamls.items():
                metaclass = dataclay_yaml_load(clazz_yaml)
                ClassLoader.deploy_metaclass_grpc(namespace, class_name, clazz_yaml, metaclass)

                if metaclass.name == "UserType" or metaclass.name == "HashType":
                    logger.warning("Ignoring %s dataClay MetaClass", metaclass.name)
                    logger.debug(metaclass)
                    continue

                if (
                    metaclass.name == "DataClayPersistentObject"
                    or metaclass.name == "DataClayObject"
                    or metaclass.name == "StorageObject"
                ):
                    continue

                logger.info(
                    "Deploying class %s to deployment source path %s",
                    metaclass.name,
                    settings.deploy_path_source,
                )

                try:
                    # ToDo: check whether `lang_codes.LANG_PYTHON` or `'LANG_PYTHON'` is the correct key here
                    import_lines = metaclass.languageDepInfos[LANG_PYTHON].imports
                    imports = "\n".join(import_lines)
                except KeyError:
                    # What is most likely is languageDepInfos not having the Python
                    imports = ""

                deploy_class(
                    metaclass.namespace,
                    metaclass.name,
                    metaclass.juxtapose_code(True),
                    imports,
                    settings.deploy_path_source,
                    ds_deploy=True,
                )
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

        logger.info("Getting MetaData for object {%s}", object_id)
        return get_runtime().get_metadata(object_id)

    def get_local_instance(self, object_id, retry=True):
        return get_runtime().get_or_new_instance_from_db(object_id, retry)

    def get_from_db(self, object_id):
        """Get object directly from StorageLocation (DB).

        :param session_id: ID of current session
        :param object_id: ID of object to get
        :return: python object
        """
        py_object = get_runtime().get_or_new_instance_from_db(object_id, True)

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

        """
        TODO: use better design for this (dgasull) 
        It is possible that a property is set to None by the GC before we 'execute' it. It should be solve by always 
        checking if loaded before returning value. Check race conditions with GC. 
        """
        if not instance.is_loaded():
            get_runtime().load_object_from_db(instance, True)

        if implementation_name.startswith(DCLAY_GETTER_PREFIX):
            prop_name = implementation_name[len(DCLAY_GETTER_PREFIX) :]
            ret_value = getattr(instance, DCLAY_PROPERTY_PREFIX + prop_name)
            # FIXME: printing value can cause __str__ call (even if __repr__ is defined)
            # FIXME: this function could be used during deserialization
            # logger.debug("Getter: for property %s returned %r", prop_name, ret_value)
            if not isinstance(ret_value, DataClayObject):
                instance.set_dirty(True)

        elif implementation_name.startswith(DCLAY_SETTER_PREFIX):
            prop_name = implementation_name[len(DCLAY_SETTER_PREFIX) :]
            # FIXME: printing value can cause __str__ call (even if __repr__ is defined)
            # FIXME: this function could be used during deserialization
            # logger.debug("Setter: for property %s (value: %r)", prop_name, params[0])
            setattr(instance, DCLAY_PROPERTY_PREFIX + prop_name, params[0])
            ret_value = None
            instance.set_dirty(True)

        else:
            logger.debug("Call: %s", implementation_name)
            dataclay_decorated_func = getattr(instance, implementation_name)
            ret_value = dataclay_decorated_func._dclay_entrypoint(instance, *params)

        return ret_value

    def set_local_session(self, session_id):
        """Set the global `threadLocal` with Session.

        :param session_id: The UUID for SessionID.
        :return: None

        Set the SessionID
        """
        # TODO: Remove thread_local_info.session_id and use the session object
        self.runtime.thread_local_data.session = self.runtime.ready_clients["@MDS"].get_session(
            session_id
        )

    def update_hints_to_current_ee(self, objects_data_to_store):
        """
        Update hints in serialized objects provided to use current backend id
        :param objects_data_to_store: serialized objects to update
        """
        ## Update hints since this function is called from other backends
        hints_mapping = dict()
        for cur_obj_data in objects_data_to_store:
            object_id = cur_obj_data.object_id
            hints_mapping[object_id] = self.execution_environment_id

        for cur_obj_data in objects_data_to_store:
            object_id = cur_obj_data.object_id
            metadata = cur_obj_data.metadata
            obj_bytes = cur_obj_data.obj_bytes
            metadata.modify_hints(hints_mapping)
            # make persistent - session references
            try:
                get_runtime().add_session_reference(object_id)
            except Exception as e:
                # TODO: See exception in set_local_session
                logger.debug(
                    "Trying to add_session_reference during store of a federated object"
                    "in a federated dataclay ==> Provided dataclayID instead of sessionID"
                )
                pass

    def store_objects(self, session_id, objects_data_to_store, moving, ids_with_alias):
        """
        @postcondition: Store objects in DB
        @param session_id: ID of session storing objects
        @param objects_data_to_store: Objects Data to store
        @param moving: Indicates if store is done during a move
        @param ids_with_alias: IDs with alias
        """

        try:
            self.set_local_session(session_id)

        except Exception as e:
            # TODO: Maybe we need to set local session and dataset in some way
            logger.debug(
                "Trying to set_local_session during store of a federated object"
                "in a federated dataclay ==> Provided dataclayID instead of sessionID"
            )
            pass

        self.update_hints_to_current_ee(objects_data_to_store)
        # store in memory
        self.store_in_memory(session_id, objects_data_to_store)

    def register_and_store_pending(self, instance, obj_bytes, sync):

        object_id = instance.get_object_id()

        # NOTE! We are doing *two* remote calls, and wishlist => they work as a transaction
        get_runtime().ready_clients["@STORAGE"].store_to_db(
            settings.environment_id, object_id, obj_bytes
        )

        # TODO: When the object metadat is updated synchronously, this should me removed
        object_md = ObjectMetadata(
            instance.get_object_id(),
            instance.get_alias(),
            instance.get_dataset_name(),
            instance.get_class_extradata().class_id,
            [settings.environment_id],
            LANG_PYTHON,
        )
        self.runtime.ready_clients["@MDS"].update_object(instance.get_owner_session_id(), object_md)

        instance.set_pending_to_register(False)

    def store_in_memory(self, session_id, objects_to_store):
        """This function will deserialize objects into dataClay memory heap using the same design as for
        volatile parameters. Eventually, dataClay GC will collect them, and then they will be
        registered in LogicModule if needed (if objects were created with alias, they must
        have metadata already).
        :param session_id: ID of session of make persistent call
        :param objects_to_store: objects to store.
        :returns: None
        :type session_id: Session ID
        :type objects_to_store:
        :rtype: None
        """
        self.set_local_session(session_id)

        # No need to provide params specs or param order since objects are not language types
        vol_objs = dict()
        i = 0
        for object_to_store in objects_to_store:
            vol_objs[i] = object_to_store
            i = i + 1
        return DeserializationLibUtilsSingleton.deserialize_params(
            SerializedParametersOrReturn(num_params=i, vol_objs=vol_objs),
            None,
            None,
            None,
            get_runtime(),
        )

    def make_persistent(self, session_id, objects_to_persist):
        """This function will deserialize make persistent "parameters" (i.e. object to persist
        and subobjects if needed) into dataClay memory heap using the same design as for
        volatile parameters. Eventually, dataClay GC will collect them, and then they will be
        registered in LogicModule if needed (if objects were created with alias, they must
        have metadata already).
        :param session_id: ID of session of make persistent call
        :param objects_to_persist: objects to store.
        :returns: None
        :type session_id: Session ID
        :type objects_to_persist:
        :rtype: None
        """
        logger.debug("Starting make persistent")
        objects = self.store_in_memory(session_id, objects_to_persist)
        for object in objects:
            # TODO: The location should be check (in the deserialization) that is the same as current ee, and reasign if not
            object_md = ObjectMetadata(
                object.get_object_id(),
                object.get_alias(),
                object.get_dataset_name(),
                object.get_class_extradata().class_id,
                [object.get_location()],
                LANG_PYTHON,
            )
            self.runtime.ready_clients["@MDS"].register_object(session_id, object_md)
        logger.debug("Finished make persistent")

    def federate(self, session_id, object_id, external_execution_env_id, recursive):
        """
        Federate object with id provided to external execution env id specified
        :param session_id: id of the session federating objects
        :param object_id: id of object to federate
        :param external_execution_id: id of dest external execution environment
        :param recursive: indicates if federation is recursive
        """
        logger.debug("----> Starting federation of %s", object_id)

        object_ids = set()
        object_ids.add(object_id)
        # TODO: check that current dataClay/EE has permission to federate the object (refederation use-case)
        serialized_objs = self.get_objects(
            session_id, object_ids, set(), recursive, external_execution_env_id, 1
        )
        client_backend = self.get_dest_ee_api(external_execution_env_id)
        client_backend.notify_federation(session_id, serialized_objs)
        # TODO: add federation reference to object send ?? how is it working with replicas?
        logger.debug("<---- Finished federation of %s", object_id)

    def notify_federation(self, session_id, objects_to_persist):
        """This function will deserialize object "parameters" (i.e. object to persist
        and subobjects if needed) into dataClay memory heap using the same design as for
        volatile parameters. This function processes objects recieved from federation calls.
        :param session_id: ID of session of federation call
        :param objects_to_persist: objects to store.
        :returns: None
        :type session_id: Session ID
        :type objects_to_persist: [num_params, imm_objs, lang_objs, vol_params, pers_params]
        """
        try:
            logger.debug("----> Notified federation")
            ## Register objects with alias
            reg_infos = list()
            for serialized_obj in objects_to_persist:
                object_id = serialized_obj.object_id
                metadata = serialized_obj.metadata
                if metadata.alias is not None and metadata.alias != "":
                    class_id = serialized_obj.class_id
                    # TODO objectID must not be replaced here by new one created by alias?
                    # FIXME: Session notifying federation does not exist, sending none
                    reg_info = RegistrationInfo(object_id, class_id, None, None, metadata.alias)
                    reg_infos.append(reg_info)
            # FIXME: remote session is retaining the object (set during deserialization) but external session is NOT closed
            # TODO: add federation reference to object send ?? how is it working with replicas?
            if len(reg_infos) != 0:
                get_runtime().ready_clients["@LM"].register_objects(
                    reg_infos, self.execution_environment_id, LANG_PYTHON
                )

            # TODO: Check that change in store_in_memory (num_params=i) dont break this.
            #       Maybe add [0] at the end of store_in_memory call (to replicate previous logic) if it has sense
            # No need to provide params specs or param order since objects are not language types
            federated_objs = self.store_in_memory(None, objects_to_persist)
            for federated_obj in federated_objs:
                try:
                    federated_obj.when_federated()
                except:
                    # ignore if method is not implemented
                    pass

        except Exception as e:
            traceback.print_exc()
            raise e
        logger.debug("<---- Finished notification of federation")

    def unfederate(self, session_id, object_id, external_execution_env_id, recursive):
        """
        Unfederate object in external execution environment specified
        :param session_id: id of session
        :param object_id: id of the object
        :param external_execution_env_id: external ee
        :param recursive: also unfederates sub-objects
        """
        # TODO: redirect unfederation to owner if current dataClay is not the owner, check origLoc belongs to current dataClay

        try:
            logger.debug("----> Starting unfederation of %s", object_id)
            object_ids = set()
            object_ids.add(object_id)
            serialized_objs = self.get_objects(
                session_id, object_ids, set(), recursive, external_execution_env_id, 2
            )

            unfederate_per_backend = dict()

            for serialized_obj in serialized_objs:
                replica_locs = serialized_obj.metadata.replica_locations
                for replica_loc in replica_locs:
                    exec_env = get_runtime().get_execution_environment_info(replica_loc)
                    if exec_env.dataclay_instance_id != get_runtime().get_dataclay_id():
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
                client_backend = self.get_dest_ee_api(external_ee_id)
                client_backend.notify_unfederation(session_id, objs_in_backend)

            logger.debug("<---- Finished unfederation of %s", object_ids)

        except Exception as e:
            traceback.print_exc()
            raise e

    def notify_unfederation(self, session_id, object_ids):
        """This function is called when objects are unfederated.
        :param session_id: ID of session of federation call
        :param object_ids: List of IDs of the objects to unfederate
        :returns: None
        :type session_id: Session ID
        :type objects_to_persist: Object ID
        """
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

                    if instance.get_alias() is not None and instance.get_alias() != "":
                        logger.debug(f"Removing alias {instance.get_alias()}")
                        self.get_runtime().delete_alias(instance)

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

    def ds_exec_impl(self, object_id, implementation_id, serialized_params_grpc_msg, session_id):
        """Perform a Remote Execute Implementation.

        See Java Implementation for details on parameters and purpose.
        """
        self.set_local_session(session_id)

        instance = self.get_local_instance(object_id, True)
        metaclass_container = instance.get_class_extradata().metaclass_container
        operation = metaclass_container.get_operation(implementation_id)
        logger.debug(f"--> Starting execution in {object_id} of operation {operation.name}")

        num_params = serialized_params_grpc_msg.num_params
        params = []
        if num_params > 0:
            params = DeserializationLibUtilsSingleton.deserialize_params(
                serialized_params_grpc_msg,
                None,
                operation.params,
                operation.paramsOrder,
                get_runtime(),
            )
        # TODO: check if any parameter is dataClay object and do not call __str__ in dClayObject could end up into a dead-lock
        # logger.debug(f"Parameters are {params}")

        ret_value = self.internal_exec_impl(operation.name, instance, params)
        result = None
        if ret_value is None:
            logger.debug("Returning None")
        else:
            logger.debug(f"Serializing return {operation.returnType.signature}")
            result = SerializationLibUtilsSingleton.serialize_params_or_return(
                {0: ret_value}, None, {"0": operation.returnType}, ["0"], None, get_runtime(), True
            )  # No volatiles inside EEs

        logger.debug(f"--> Finished execution in {object_id} of operation {operation.name}")
        return result

    def new_persistent_instance(self, payload):
        """Create, make persistent and return an instance for a certain class."""

        raise NotImplementedError(
            "NewPersistentInstance RPC is not yet ready (@ Python ExecutionEnvironment)"
        )

    def get_dest_ee_api(self, dest_backend_id):
        """
        Get API to connect to destination Execution environment with id provided
        :param dest_backend_id: ID of destination backend
        :return: API to connect to destination Execution environment with id provided
        """
        backend = get_runtime().get_execution_environment_info(dest_backend_id)
        try:
            client_backend = get_runtime().ready_clients[dest_backend_id]
        except KeyError:
            logger.verbose(
                "Not found Client to ExecutionEnvironment {%s}!" " Starting it at %s:%d",
                dest_backend_id,
                backend.hostname,
                backend.port,
            )
            client_backend = EEClient(backend.hostname, backend.port)
            get_runtime().ready_clients[dest_backend_id] = client_backend
        return client_backend

    def new_replica(self, session_id, object_id, dest_backend_id, recursive):
        """Creates a new replica of the object with ID provided in the backend specified.

        :param session_id: ID of session
        :param object_id: ID of the object
        :param dest_backend_id: destination backend id
        :param recursive: Indicates if all sub-objects must be replicated as well.

        :return: None
        """
        logger.debug("----> Starting new replica of %s to backend %s", object_id, dest_backend_id)

        object_ids = set()
        object_ids.add(object_id)
        serialized_objs = self.get_objects(
            session_id, object_ids, set(), recursive, dest_backend_id, 1
        )
        client_backend = self.get_dest_ee_api(dest_backend_id)
        client_backend.ds_store_objects(session_id, serialized_objs, False, None)
        replicated_ids = set()
        for serialized_obj in serialized_objs:
            replicated_ids.add(serialized_obj.object_id)
        logger.debug("<---- Finished new replica of %s", object_id)
        return replicated_ids

    def synchronize(
        self, session_id, object_id, implementation_id, serialized_value, calling_backend_id=None
    ):
        # set field
        logger.debug(
            f"----> Starting synchronization of {object_id} from calling backend {calling_backend_id}"
        )

        self.ds_exec_impl(object_id, implementation_id, serialized_value, session_id)
        instance = self.get_local_instance(object_id, True)
        src_exec_env_id = instance.get_origin_location()
        if src_exec_env_id is not None:
            logger.debug(f"Found origin location {src_exec_env_id}")
            if calling_backend_id is None or src_exec_env_id != calling_backend_id:
                # do not synchronize to calling source (avoid infinite loops)
                dest_backend = self.get_dest_ee_api(src_exec_env_id)
                logger.debug(
                    f"----> Propagating synchronization of {object_id} to origin location {src_exec_env_id}"
                )

                dest_backend.synchronize(
                    session_id,
                    object_id,
                    implementation_id,
                    serialized_value,
                    calling_backend_id=self.execution_environment_id,
                )

        replica_locations = instance.get_replica_locations()
        if replica_locations is not None:
            logger.debug(f"Found replica locations {replica_locations}")
            for replica_location in replica_locations:
                if calling_backend_id is None or replica_location != calling_backend_id:
                    # do not synchronize to calling source (avoid infinite loops)
                    dest_backend = self.get_dest_ee_api(replica_location)
                    logger.debug(
                        f"----> Propagating synchronization of {object_id} to replica location {replica_location}"
                    )
                    dest_backend.synchronize(
                        session_id,
                        object_id,
                        implementation_id,
                        serialized_value,
                        calling_backend_id=self.execution_environment_id,
                    )
        logger.debug(f"----> Finished synchronization of {object_id}")

    def get_copy_of_object(self, session_id, object_id, recursive):
        """Returns a non-persistent copy of the object with ID provided

        :param session_id: ID of session
        :param object_id: ID of the object
        :return: the generated non-persistent objects
        """
        logger.debug("[==Get==] Get copy of %s ", object_id)

        # Get the data service of one of the backends that contains the original object.
        object_ids = set()
        object_ids.add(object_id)

        serialized_objs = self.get_objects(session_id, object_ids, set(), recursive, None, 0)

        # Prepare OIDs
        logger.debug("[==Get==] Serialized objects obtained to create a copy of %s", object_id)
        original_to_version = dict()

        # Store version in this backend (if already stored, just skip it)
        for obj_with_param_or_return in serialized_objs:
            orig_obj_id = obj_with_param_or_return.object_id
            version_obj_id = uuid.uuid4()
            original_to_version[orig_obj_id] = version_obj_id

        for obj_with_param_or_return in serialized_objs:
            orig_obj_id = obj_with_param_or_return.object_id
            version_obj_id = original_to_version[orig_obj_id]
            metadata = obj_with_param_or_return.metadata
            self._modify_metadata_oids(metadata, original_to_version)
            obj_with_param_or_return.object_id = version_obj_id

        i = 0
        imm_objs = dict()
        lang_objs = dict()
        vol_params = dict()
        pers_params = dict()
        for obj in serialized_objs:
            vol_params[i] = obj
            i = i + 1

        serialized_result = SerializedParametersOrReturn(
            num_params=i,
            imm_objs=imm_objs,
            lang_objs=lang_objs,
            vol_objs=vol_params,
            pers_objs=pers_params,
        )

        return serialized_result

    def update_object(self, session_id, into_object_id, from_object):
        """Updates an object with ID provided with contents from another object
        :param session_id: ID of session
        :param into_object_id: ID of the object to be updated
        :param from_object: object with contents to be used
        """
        self.set_local_session(session_id)
        logger.debug("[==PutObject==] Updating object %s", into_object_id)
        object_into = get_runtime().get_or_new_instance_from_db(into_object_id, False)
        object_from = DeserializationLibUtilsSingleton.deserialize_params_or_return(
            from_object, None, None, None, get_runtime()
        )[0]
        object_into.set_all(object_from)
        logger.debug(
            "[==PutObject==] Updated object %s from object %s",
            into_object_id,
            object_from.get_object_id(),
        )

    def get_objects(
        self,
        session_id,
        object_ids,
        already_obtained_objs,
        recursive,
        dest_replica_backend_id=None,
        update_replica_locs=0,
    ):
        """Get the serialized objects with id provided
        :param session_id: ID of session
        :param object_ids: IDs of the objects to get
        :param recursive: Indicates if, per each object to get, also obtain its associated objects.
        :param dest_replica_backend_id: Destination backend of objects being obtained for replica or NULL if going to client
        :param update_replica_locs: If 1, provided replica dest backend id must be added to replica locs of obtained objects
                               If 2, provided replica dest backend id must be removed from replica locs
                               If 0, replicaDestBackendID field is ignored
        :return: List of serialized objects
        """
        logger.debug("[==Get==] Getting objects %s", object_ids)

        self.set_local_session(session_id)

        result = list()
        pending_oids_and_hint = list()
        objects_in_other_backend = list()

        for oid in object_ids:
            if recursive:
                # Add object to pending
                pending_oids_and_hint.append([oid, None])
                while pending_oids_and_hint:
                    current_oid_and_hint = pending_oids_and_hint.pop()
                    current_oid = current_oid_and_hint[0]
                    current_hint = current_oid_and_hint[1]
                    if current_oid in already_obtained_objs:
                        # Already Read
                        logger.verbose("[==Get==] Object %s already read", current_oid)
                        continue
                    if current_hint is not None and current_hint != self.execution_environment_id:
                        # in another backend
                        objects_in_other_backend.append([current_oid, current_hint])
                        continue

                    else:
                        try:
                            logger.verbose(
                                "[==Get==] Trying to get local instance for object %s", current_oid
                            )
                            obj_with_data = self.get_object_internal(
                                current_oid, dest_replica_backend_id, update_replica_locs
                            )
                            if obj_with_data is not None:
                                result.append(obj_with_data)
                                already_obtained_objs.add(current_oid)
                                # Get associated objects and add them to pendings
                                obj_metadata = obj_with_data.metadata
                                for tag in obj_metadata.tags_to_oids:
                                    oid_found = obj_metadata.tags_to_oids[tag]
                                    hint_found = obj_metadata.tags_to_hints[tag]
                                    if (
                                        oid_found != current_oid
                                        and oid_found not in already_obtained_objs
                                    ):
                                        pending_oids_and_hint.append([oid_found, hint_found])

                        except:
                            traceback.print_exc()
                            logger.debug(
                                f"[==Get==] Not in this backend (wrong or null hint) for {current_oid}"
                            )
                            # Get in other backend (remove hint, it failed here)
                            objects_in_other_backend.append([current_oid, None])
            else:
                try:
                    obj_with_data = self.get_object_internal(
                        oid, dest_replica_backend_id, update_replica_locs
                    )
                    if obj_with_data is not None:
                        result.append(obj_with_data)
                except:
                    logger.debug("[==Get==] Object is in other backend")
                    # Get in other backend
                    objects_in_other_backend.append([oid, None])

        obj_with_data_in_other_backends = self.get_objects_in_other_backends(
            session_id,
            objects_in_other_backend,
            already_obtained_objs,
            recursive,
            dest_replica_backend_id,
            update_replica_locs,
        )

        for obj_in_oth_back in obj_with_data_in_other_backends:
            result.append(obj_in_oth_back)
        logger.debug("[==Get==] Finished get objects len = %s", str(len(result)))
        return result

    def get_object_internal(self, oid, dest_replica_backend_id, update_replica_locs):
        """Get object internal function
        :param oid: ID of the object ot get
        :param dest_replica_backend_id: Destination backend of objects being obtained for replica or NULL if going to client
        :param update_replica_locs: If 1, provided replica dest backend id must be added to replica locs of obtained objects
                               If 2, provided replica dest backend id must be removed from replica locs
                               If 0, replicaDestBackendID field is ignored
        :return: Object with data
        :type oid: ObjectID
        :rtype: Object with data
        """
        # Serialize the object
        logger.verbose("[==GetInternal==] Trying to get local instance for object %s", oid)

        # ToDo: Manage better this try/catch
        get_runtime().lock(
            oid
        )  # Race condition with gc: make sure GC does not CLEAN the object while retrieving/serializing it!
        try:
            current_obj = self.get_local_instance(oid, False)
            pending_objs = list()

            # update_replica_locs = 1 means new replica/federation
            if dest_replica_backend_id is not None and update_replica_locs == 1:
                if current_obj.get_replica_locations() is not None:
                    if dest_replica_backend_id in current_obj.get_replica_locations():
                        # already replicated
                        logger.debug(f"WARNING: Found already replicated object {oid}. Skipping")
                        return None

            # Add object to result and obtained_objs for return and recursive
            obj_with_data = SerializationLibUtilsSingleton.serialize_dcobj_with_data(
                current_obj, pending_objs, False, current_obj.get_hint(), get_runtime(), False
            )

            if dest_replica_backend_id is not None and update_replica_locs == 1:
                current_obj.add_replica_location(dest_replica_backend_id)
                current_obj.set_dirty(True)
                obj_with_data.metadata.origin_location = self.execution_environment_id
            elif update_replica_locs == 2:
                if dest_replica_backend_id is not None:
                    current_obj.remove_replica_location(dest_replica_backend_id)
                else:
                    current_obj.clear_replica_locations()
                current_obj.set_dirty(True)

        finally:
            get_runtime().unlock(oid)
        return obj_with_data

    def get_objects_in_other_backends(
        self,
        session_id,
        objects_in_other_backend,
        already_obtained_objs,
        recursive,
        dest_replica_backend_id,
        update_replica_locs,
    ):
        """Get object in another backend. This function is called from DbHandler in a recursive get.

        :param session_id: ID of session
        :param objects_in_other_backend: List of metadata of objects to read. It is useful to avoid multiple trips.
        :param recursive: Indicates is recursive
        :param dest_replica_backend_id: Destination backend of objects being obtained for replica or NULL if going to client
        :param update_replica_locs: If 1, provided replica dest backend id must be added to replica locs of obtained objects
                               If 2, provided replica dest backend id must be removed from replica locs
                               If 0, replicaDestBackendID field is ignored
        :return: List of serialized objects
        """
        result = list()

        # Prepare to unify calls (only one call for DS)
        objects_per_backend = dict()

        for curr_oid_and_hint in objects_in_other_backend:
            curr_oid = curr_oid_and_hint[0]
            curr_hint = curr_oid_and_hint[1]

            if curr_hint is not None:
                location = curr_hint
            else:

                logger.debug("[==GetObjectsInOtherBackend==] Looking for metadata of %s", curr_oid)

                metadata = self.get_object_metadatainfo(curr_oid)
                logger.info("metadata info are %s", metadata)

                if metadata is None:
                    raise Exception("!!! Object %s without hint and metadata not found" % curr_oid)

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

            if dest_replica_backend_id is None or dest_replica_backend_id != backend_id:

                logger.debug(
                    "[==GetObjectsInOtherBackend==] Get from other location, objects: %s",
                    objects_to_get,
                )
                backend = get_runtime().get_all_execution_environments_info()[backend_id]
                try:
                    client_backend = get_runtime().ready_clients[backend_id]
                except KeyError:
                    logger.verbose(
                        "[==GetObjectsInOtherBackend==] Not found Client to ExecutionEnvironment {%s}!"
                        " Starting it at %s:%d",
                        backend_id,
                        backend.hostname,
                        backend.port,
                    )

                    client_backend = EEClient(backend.hostname, backend.port)
                    get_runtime().ready_clients[backend_id] = client_backend

                cur_result = client_backend.ds_get_objects(
                    session_id,
                    objects_to_get,
                    already_obtained_objs,
                    recursive,
                    dest_replica_backend_id,
                    update_replica_locs,
                )
                logger.verbose(
                    "[==GetObjectsInOtherBackend==] call return length: %d", len(cur_result)
                )
                logger.trace("[==GetObjectsInOtherBackend==] call return content: %s", cur_result)
                for res in cur_result:
                    result.append(res)

        return result

    def new_version(self, session_id, object_id, dest_backend_id):
        """Creates a new version of the object with ID provided in the backend specified.

        :param session_id: ID of session
        :param object_id: ID of the object
        :param dest_backend_id: Destination in which version must be created
        """
        logger.debug("----> Starting new version of %s", object_id)

        # Get the data service of one of the backends that contains the original object.
        object_ids = set()
        object_ids.add(object_id)
        serialized_objs = self.get_objects(session_id, object_ids, set(), True, None, 1)

        # Prepare OIDs
        original_to_version = dict()

        # Store version in this backend (if already stored, just skip it)
        for obj_with_data in serialized_objs:
            orig_obj_id = obj_with_data.object_id
            version_obj_id = uuid.uuid4()
            original_to_version[orig_obj_id] = version_obj_id

        for obj_with_param_or_return in serialized_objs:
            orig_obj_id = obj_with_param_or_return.object_id
            version_obj_id = original_to_version[orig_obj_id]
            metadata = obj_with_param_or_return.metadata
            self._modify_metadata_oids(metadata, original_to_version)
            if metadata.orig_object_id is None:
                # IMPORTANT: only set if not already set since consolidate
                # is always applied to original one
                metadata.orig_object_id = orig_obj_id
                metadata.root_location = self.execution_environment_id
            obj_with_param_or_return.object_id = version_obj_id

        if dest_backend_id == self.execution_environment_id:
            self.store_objects(session_id, serialized_objs, False, None)
        else:
            client_backend = self.get_dest_ee_api(dest_backend_id)
            client_backend.ds_store_objects(session_id, serialized_objs, False, None)
        version_obj_id = original_to_version[object_id]
        logger.debug(f"<---- Finished new version of {object_id} as {version_obj_id}")
        return version_obj_id

    def consolidate_version(self, session_id, final_version_id):
        """Consolidates object with id provided
        :param session_id:ID of session
        :param final_version_id: ID of final version object
        """
        self.set_local_session()
        logger.debug("----> Starting consolidate version of %s", final_version_id)

        # Consolidate in this backend - the complete version is here
        object_ids = set()
        object_ids.add(final_version_id)
        serialized_objs = self.get_objects(session_id, object_ids, set(), True, None, 0)

        root_location = None

        version_to_original = dict()
        for serialized_obj in serialized_objs:
            version_id = serialized_obj.object_id
            original_md = serialized_obj.metadata
            if original_md.orig_object_id is not None:
                version_to_original[version_id] = original_md.orig_object_id
            if version_id == final_version_id:
                root_location = original_md.root_location

        serialized_objs_updated = list()
        for serialized_obj in serialized_objs:
            original_md = serialized_obj.metadata
            self._modify_metadata_oids(original_md, version_to_original)
            if original_md.orig_object_id is not None:
                serialized_obj.object_id = original_md.orig_object_id
            serialized_objs_updated.append(serialized_obj)

        try:
            if root_location == self.execution_environment_id:
                self.upsert_objects(session_id, serialized_objs_updated)
            else:
                client_backend = self.get_dest_ee_api(root_location)
                client_backend.ds_upsert_objects(session_id, serialized_objs_updated)
        except Exception as e:
            traceback.print_exc()
            logger.error("Exception during Consolidate Version")
            raise e
        logger.debug("<---- Finished consolidate of %s", final_version_id)

    def _modify_metadata_oids(self, metadata, original_to_version):
        """Modify the version's metadata in serialized_objs with original OID"""
        logger.debug("[==ModifyMetadataOids==] Modify metadata object %r", metadata)
        logger.debug("[==ModifyMetadataOids==] Version OIDs Map: %s", original_to_version)

        for tag, oid in metadata.tags_to_oids.items():
            try:
                metadata.tags_to_oids[tag] = original_to_version[oid]
            except KeyError:
                logger.debug(
                    "[==ModifyMetadataOids==] oid %s is not mapped => object added in the version",
                    oid,
                )
                # obj[2][0][tag] = oid
                pass

        logger.debug("[==ModifyMetadataOids==] Object with modified metadata is %r", metadata)

    def upsert_objects(self, session_id, object_ids_and_bytes):
        """Updates objects or insert if they do not exist with the values in objectBytes.
        NOTE: This function is recursive, it is going to other DSs if needed.
        :param session_id: ID of session needed.
        :param object_ids_and_bytes: Map of objects to update.
        """
        self.set_local_session()

        try:
            objects_in_other_backends = list()
            updated_objects_here = list()

            # To check for replicas
            for cur_entry in object_ids_and_bytes:
                # ToDo: G.C. stuffs
                object_id = cur_entry.object_id
                logger.debug("[==Upsert==] Updated or inserted object %s", object_id)
                try:
                    # Update bytes at memory object
                    logger.debug(
                        "[==Upsert==] Getting/Creating instance from upsert with id %s", object_id
                    )
                    instance = get_runtime().get_or_new_instance_from_db(object_id, False)
                    DeserializationLibUtilsSingleton.deserialize_object_with_data(
                        cur_entry,
                        instance,
                        None,
                        get_runtime(),
                        get_runtime().get_session().id,
                        True,
                    )

                    instance.set_dirty(True)
                    updated_objects_here.append(cur_entry)
                except Exception:
                    # Get in other backend
                    objects_in_other_backends.append(cur_entry)

            self.update_hints_to_current_ee(updated_objects_here)
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

            backend = (
                get_runtime()
                .ready_clients["@LM"]
                .get_executionenvironment_info(backend_id, from_backend=True)
            )

            try:
                client_backend = get_runtime().ready_clients[backend_id]
            except KeyError:
                logger.verbose(
                    "[==GetObjectsInOtherBackend==] Not found Client to ExecutionEnvironment {%s}!"
                    " Starting it at %s:%d",
                    backend_id,
                    backend.hostname,
                    backend.port,
                )

                client_backend = EEClient(backend.hostname, backend.port)
                get_runtime().ready_clients[backend_id] = client_backend

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
            logger.debug(
                "[==MoveObjects==] Moving object %s to storage location: %s",
                object_id,
                dest_backend_id,
            )
            object_ids = set()
            object_ids.add(object_id)

            # TODO: Object being used by session (any oid in the method header) G.C.

            serialized_objs = self.get_objects(session_id, object_ids, set(), True, None, 0)
            objects_to_remove = set()
            objects_to_move = list()

            for obj_found in serialized_objs:
                logger.debug("[==MoveObjects==] Looking for metadata of %s", obj_found[0])
                metadata = self.get_object_metadatainfo(obj_found[0])
                obj_location = list(metadata.locations.keys())[0]

                if obj_location == dest_backend_id:
                    logger.debug(
                        "[==MoveObjects==] Ignoring move of object %s since it is already where it should be."
                        " ObjLoc = %s and DestLoc = %s",
                        obj_found[0],
                        obj_location,
                        dest_backend_id,
                    )

                    # object already in dest
                    pass
                else:
                    if settings.storage_id == dest_backend_id:
                        # THE DESTINATION IS HERE
                        if obj_location != settings.storage_id:
                            logger.debug(
                                "[==MoveObjects==] Moving object  %s since dest.location is different to src.location and object is not in dest.location."
                                " ObjLoc = %s and DestLoc = %s",
                                obj_found[0],
                                obj_location,
                                dest_backend_id,
                            )
                            objects_to_move.append(obj_found)
                            objects_to_remove.add(obj_found[0])
                            update_metadata_of.add(obj_found[0])
                        else:
                            logger.debug(
                                "[==MoveObjects==] Ignoring move of object %s since it is already where it should be"
                                " ObjLoc = %s and DestLoc = %s",
                                obj_found[0],
                                obj_location,
                                dest_backend_id,
                            )
                    else:
                        logger.debug(
                            "[==MoveObjects==] Moving object %s since dest.location is different to src.location and object is not in dest.location "
                            " ObjLoc = %s and DestLoc = %s",
                            obj_found[0],
                            obj_location,
                            dest_backend_id,
                        )
                        # THE DESTINATION IS ANOTHER NODE: move.
                        objects_to_move.append(obj_found)
                        objects_to_remove.add(obj_found[0])
                        update_metadata_of.add(obj_found[0])

            logger.debug("[==MoveObjects==] Finally moving OBJECTS: %s", objects_to_remove)

            try:
                sl_client = get_runtime().ready_clients[dest_backend_id]
            except KeyError:
                st_loc = get_runtime().get_all_execution_environments_info()[dest_backend_id]
                logger.debug(
                    "Not found in cache ExecutionEnvironment {%s}! Starting it at %s:%d",
                    dest_backend_id,
                    st_loc.hostname,
                    st_loc.port,
                )
                sl_client = EEClient(st_loc.hostname, st_loc.port)
                get_runtime().ready_clients[dest_backend_id] = sl_client

            sl_client.ds_store_objects(session_id, objects_to_move, True, None)

            # TODO: lock any execution in remove before storing objects in remote dataservice so anyone can modify it.
            # Remove after store in order to avoid wrong executions during the movement :)
            # Remove all objects in all source locations different to dest. location
            # TODO: Check that remove is not necessary (G.C. Should do it?)
            # get_runtime().ready_clients["@STORAGE"].ds_remove_objects(session_id, object_ids, recursive, True, dest_backend_id)

            for oid in objects_to_remove:
                get_runtime().remove_metadata_from_cache(oid)
            logger.debug("[==MoveObjects==] Move finalized ")

        except Exception as e:
            logger.error("[==MoveObjects==] Exception %s", e.args)

        return update_metadata_of

    def update_refs(self, ref_counting):
        """forward to SL"""
        get_runtime().ready_clients["@STORAGE"].update_refs(ref_counting)

    def get_retained_references(self):
        return self.runtime.get_retained_references()

    def close_session_in_ee(self, session_id):
        self.runtime.close_session_in_ee(session_id)

    def detach_object_from_session(self, object_id, session_id):
        logger.debug(f"--> Detaching object {object_id} from session {session_id}")
        self.set_local_session(session_id)
        self.runtime.detach_object_from_session(object_id, None)
        logger.debug(f"<-- Detached object {object_id} from session {session_id}")

    def delete_alias(self, session_id, object_id):
        self.set_local_session(session_id)
        instance = self.get_local_instance(object_id, True)
        self.runtime.delete_alias(instance)

    def exists(self, object_id):
        self.runtime.lock(object_id)  # RACE CONDITION: object is being unloaded but still not in SL
        # object might be in heap but as a "proxy"
        # since this function is used from SL after checking if the object is in database,
        # we return false if the object is not loaded so the combination of SL exists and EE exists
        # can tell if the object actually exists
        # summary: the object only exist in EE if it is loaded.
        try:
            in_heap = self.runtime.exists(object_id)
            if in_heap:
                obj = self.runtime.get_from_heap(object_id)
                return obj.is_loaded()
            else:
                return False
        finally:
            self.runtime.unlock(object_id)

    def get_num_objects(self):
        return self.runtime.count_loaded_objs()

    def get_traces(self):
        logger.debug("Merging...")
        return get_traces()

    ################## EXTRAE IGNORED FUNCTIONS ###########################
    deactivate_tracing.do_not_trace = True
    activate_tracing.do_not_trace = True
