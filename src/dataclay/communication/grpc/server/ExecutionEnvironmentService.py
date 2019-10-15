
""" Class description goes here. """

"""gRPC ExecutionEnvironment Server code - StorageLocation/EE methods."""

from io import BytesIO
import logging
import traceback
import six

if six.PY2:
    import cPickle as pickle
elif six.PY3:
    import _pickle as pickle

from dataclay.commonruntime.Runtime import getRuntime
from dataclay.communication.grpc import Utils
from dataclay.communication.grpc.generated.dataservice import dataservice_pb2_grpc as ds
from dataclay.communication.grpc.messages.common import common_messages_pb2
from dataclay.communication.grpc.messages.dataservice import dataservice_messages_pb2
from dataclay.exceptions.exceptions import DataClayException
from dataclay.util.YamlParser import dataclay_yaml_load

__author__ = 'Enrico La Sala <enrico.lasala@bsc.es>'
__copyright__ = '2017 Barcelona Supercomputing Center (BSC-CNS)'

logger = logging.getLogger(__name__)

_ONE_DAY_IN_SECONDS = 60 * 60 * 24


class DataServiceEE(ds.DataServiceServicer):

    interceptor = None

    def __init__(self, theexec_env, interceptor=None):
        """ Execution environment being managed """
        self.execution_environment = theexec_env
        DataServiceEE.interceptor = interceptor
        
    def ass_client(self):
        self.client = getRuntime().ready_clients["@STORAGE"]

    def get_exception_info(self, ex):
        ex_message = None
        if hasattr(ex, "message"):
            ex_message = ex.message
            logger.warning("Exception produced with message:\n%s", ex_message)

        try:
            ex_serialized = pickle.dumps(ex)
        except TypeError:
            logger.warning("Could not serialize %s", ex)
            ex_serialized = None

        return common_messages_pb2.ExceptionInfo(
                isException=True,
                serializedException=ex_serialized,
                exceptionMessage=Utils.prepare_exception(ex_message, Utils.return_stack())
            )

    def deployMetaClasses(self, request, context):
        
        logger.verbose("[deployMetaClasses] Deploying classes")

        try:
            namespace = request.namespace
            classes_map_yamls = request.deploymentPack 
            self.execution_environment.ds_deploy_metaclasses(namespace, classes_map_yamls)
            return common_messages_pb2.ExceptionInfo()

        except Exception as ex:
            return self.get_exception_info(ex)

    def newPersistentInstance(self, request, context):

        try:
            iface_bit_maps = {}

            for k, v in request.ifaceBitMaps.items():
                iface_bit_maps[Utils.get_id_from_uuid(k)] = Utils.prepare_bytes(v)

            params = []

            if request.params:
                params = Utils.get_param_or_return(request.params)

            oid = self.client.ds_new_persistent_instance(Utils.get_id(request.sessionID),
                                                         Utils.get_id(request.classID),
                                                         Utils.get_id(request.implementationID),
                                                         iface_bit_maps,
                                                         params)

            return dataservice_messages_pb2.NewPersistentInstanceResponse(objectID=Utils.get_msg_options['object'](oid))

        except Exception as ex:
            return dataservice_messages_pb2.NewPersistentInstanceResponse(
                excInfo=self.get_exception_info(ex))

    def storeObjects(self, request, context):
                
        try:
            objects_list = []
            for vol_param in request.objects:
                param = Utils.get_obj_with_data_param_or_return(vol_param)
                serialized_obj = BytesIO(param[3])
                dcobj = param[0], param[1], param[2], serialized_obj
                objects_list.append(dcobj)

            ids_with_alias_set = set()
            session_id = Utils.get_id(request.sessionID)
            if request.idsWithAlias is not None and len(request.idsWithAlias) > 0:
                for ids_with_alias in request.idsWithAlias:
                    ids_with_alias_set.add(Utils.get_id(ids_with_alias))

            self.execution_environment.store_objects(session_id, objects_list, request.moving, ids_with_alias_set)
            return common_messages_pb2.ExceptionInfo()

        except Exception as ex:
            return self.get_exception_info(ex)
    
    def makePersistent(self, request, context):
        try:
            objects_to_persist = Utils.get_param_or_return(request.params)
            session_id = Utils.get_id(request.sessionID)
            self.execution_environment.make_persistent(session_id, objects_to_persist)
            logger.verbose("MakePersistent finished, sending response")
            return common_messages_pb2.ExceptionInfo()

        except Exception as ex:
            traceback.print_exc()
            return self.get_exception_info(ex)
            
    def federate(self, request, context):
        try:
            logger.verbose("Federation started")
            objects_to_persist = Utils.get_param_or_return(request.params)
            session_id = Utils.get_id(request.sessionID)
            self.execution_environment.federate(session_id, objects_to_persist)
            logger.verbose("Federation finished, sending response")
            return common_messages_pb2.ExceptionInfo()

        except Exception as ex:
            return self.get_exception_info(ex)

    def unfederate(self, request, context):
        try:
            logger.verbose("Unfederation started")
            session_id = Utils.get_id(request.sessionID)
            object_ids = set()
            for oid in request.objectIDs:
                object_ids.add(Utils.get_id(oid))
            self.execution_environment.unfederate(session_id, object_ids)
            logger.verbose("Unfederation finished, sending response")
            return common_messages_pb2.ExceptionInfo()

        except Exception as ex:
            traceback.print_exc()
            return self.get_exception_info(ex)

    def executeImplementation(self, request, context):
        logger.debug("Starting ExecuteImplementation handling")

        try:
            object_id = Utils.get_id(request.objectID)
            implementation_id = Utils.get_id(request.implementationID)
            serialized_params = Utils.get_param_or_return(request.params)
            session_id = Utils.get_id(request.sessionID)
            result = self.execution_environment.ds_exec_impl(object_id, implementation_id, serialized_params, session_id)
            logger.verbose("ExecuteImplementation finished, sending response")

            return dataservice_messages_pb2.ExecuteImplementationResponse(ret=Utils.get_param_or_return(result))

        except Exception as ex:
            traceback.print_exc()
            return dataservice_messages_pb2.ExecuteImplementationResponse(
                excInfo=self.get_exception_info(ex))

    def getCopyOfObject(self, request, context):
        try:
            result = self.execution_environment.get_copy_of_object(
                Utils.get_id(request.sessionID),
                Utils.get_id(request.objectID),
                request.recursive)
            
            return dataservice_messages_pb2.GetCopyOfObjectResponse(ret=Utils.get_param_or_return(result))
        
        except Exception as ex:
            return dataservice_messages_pb2.GetObjectsResponse(
                excInfo=self.get_exception_info(ex)
            )
            
    def updateObject(self, request, context):
        try:
            
            self.execution_environment.update_object(
                Utils.get_id(request.sessionID),
                Utils.get_id(request.intoObjectID),
                Utils.get_param_or_return(request.fromObject)
                )
            
            logger.verbose("updateObject finished, sending response")
            
            return common_messages_pb2.ExceptionInfo()

        except DataClayException as ex:
            return self.get_exception_info(ex)

    def getObjects(self, request, context):
        try:
            object_ids = set()
            for oid in request.objectIDS:
                object_ids.add(Utils.get_id(oid))

            result = self.execution_environment.get_objects(Utils.get_id(request.sessionID),
                                            object_ids,
                                            request.recursive,
                                            request.moving)

            obj_list = []

            for entry in result:
                obj_list.append(Utils.get_obj_with_data_param_or_return(entry))

            return dataservice_messages_pb2.GetObjectsResponse(objects=obj_list)

        except Exception as ex:
            return dataservice_messages_pb2.GetObjectsResponse(
                excInfo=self.get_exception_info(ex)
            )

    def getReferencedObjectsIDs(self, request, context):
        try:
            object_ids = set()
            for oid in request.objectIDS:
                object_ids.add(Utils.get_id(oid))
            
            result = self.execution_environment.get_referenced_objects_ids(
                                            Utils.get_id(request.sessionID),
                                            object_ids)
            obj_list = []
            for entry in result:
                obj_list.append(Utils.get_msg_options['object'](entry))
    
            return dataservice_messages_pb2.GetReferencedObjectIDsResponse(objectIDs=obj_list)

        except Exception as ex:
            return dataservice_messages_pb2.GetReferencedObjectIDsResponse(
                excInfo=self.get_exception_info(ex)
            )

    def getFederatedObjects(self, request, context):
        try:
            object_ids = set()
            for oid in request.objectIDS:
                object_ids.add(Utils.get_id(oid))
            
            result = self.execution_environment.get_federated_objects(
                Utils.get_id(request.extDataClayID),
                object_ids
            )
            obj_list = []

            for entry in result:
                obj_list.append(Utils.get_obj_with_data_param_or_return(entry))
    
            return dataservice_messages_pb2.GetFederatedObjectsResponse(objects=obj_list)

        except DataClayException as ex:
            return dataservice_messages_pb2.GetFederatedObjectsResponse(
                excInfo=self.get_exception_info(ex)
            )

    def newMetaData(self, request, context):

        try:
            md_infos = {}

            for k, v in request.mdInfos.items():

                md_infos[Utils.get_id_from_uuid(k)] = dataclay_yaml_load(v)

            self.client.ds_new_metadata(md_infos)

            return common_messages_pb2.ExceptionInfo()

        except Exception as ex:
            return self.get_exception_info(ex)

    def newVersion(self, request, context):

        try:
            result = self.execution_environment.new_version(
                Utils.get_id(request.sessionID),
                Utils.get_id(request.objectID),
                dataclay_yaml_load(request.metadataInfo)
            )

            vers_ids = dict()

            for k, v in result[1].items():
                vers_ids[Utils.prepare_bytes(str(k))] = Utils.prepare_bytes(str(v))

            return dataservice_messages_pb2.NewVersionResponse(
                objectID=Utils.get_msg_options['object'](result[0]),
                versionedIDs=vers_ids
            )

        except Exception as ex:
            return dataservice_messages_pb2.NewVersionResponse(
                excInfo=self.get_exception_info(ex)
            )

    def consolidateVersion(self, request, context):

        try:
            self.execution_environment.consolidate_version(Utils.get_id(request.sessionID),
                                           dataclay_yaml_load(request.versionInfo))

            return common_messages_pb2.ExceptionInfo()

        except Exception as ex:
            return self.get_exception_info(ex)

    def upsertObjects(self, request, context):

        try:
            session_id = Utils.get_id(request.sessionID)

            objects = []
            for entry in request.bytesUpdate:
                objects.append(Utils.get_obj_with_data_param_or_return(entry))

            self.execution_environment.upsert_objects(session_id, objects)

            return common_messages_pb2.ExceptionInfo()

        except Exception as ex:
            return self.get_exception_info(ex)

    def newReplica(self, request, context):

        ##### NOT WELL IMPL. NEW ALGORITHM MISSING FOR MOVING OBJECTS CHECKING FIRST THE MEMORY ######

        try:
            result = self.execution_environment.new_replica(Utils.get_id(request.sessionID),
                                            Utils.get_id(request.objectID),
                                            request.recursive)

            repl_ids_list = []

            for oid in result:
                repl_ids_list.append(Utils.get_msg_options['object'](oid))

            return dataservice_messages_pb2.NewReplicaResponse(
                replicatedIDs=repl_ids_list
            )

        except Exception as ex:
            traceback.print_exc()
            return dataservice_messages_pb2.NewReplicaResponse(
                excInfo=self.get_exception_info(ex)
            )

    def moveObjects(self, request, context):

        ##### NOT WELL IMPL. NEW ALGORITHM MISSING FOR MOVING OBJECTS CHECKING FIRST THE MEMORY ######

        try:
            result = self.execution_environment.move_objects(Utils.get_id(request.sessionID),
                                                 Utils.get_id(request.objectID),
                                                 Utils.get_id(request.destLocID),
                                                 request.recursive)

            mov_obj_list = []

            for oid in result:
                mov_obj_list.append(Utils.get_msg_options['object'](oid))

            return dataservice_messages_pb2.MoveObjectsResponse(
                movedObjects=mov_obj_list
            )

        except Exception as ex:
            return dataservice_messages_pb2.MoveObjectsResponse(
                excInfo=self.get_exception_info(ex)
            )

    def removeObjects(self, request, context):

        try:
            object_ids = set()

            for oid in request.getObjectsIDSList():
                object_ids.add(Utils.get_id(oid))

            result = self.client.ds_remove_objects(Utils.get_id(request.sessionID),
                                                   object_ids,
                                                   request.recursive,
                                                   request.moving,
                                                   Utils.get_id(request.newHint))

            rem_obj = dict()

            for k, v in result.items():
                rem_obj[str(k)] = str(v)

            return dataservice_messages_pb2.RemoveObjectsResponse(
                removedObjects=rem_obj
            )

        except Exception as ex:
            return dataservice_messages_pb2.RemoveObjectsResponse(
                excInfo=self.get_exception_info(ex)
            )
    
    def exists(self, request, context):
        try: 
            exists = self.execution_environment.exists(Utils.get_id(request.objectID))
            return dataservice_messages_pb2.ExistsResponse(
                exists=exists
            )
        except Exception as ex:
            return dataservice_messages_pb2.ExistsResponse(
                excInfo=self.get_exception_info(ex)
            )
    
    def updateRefs(self, request, context):
        try: 

            """ deserialize into dictionary of object id - integer """ 
            ref_counting = dict() 
            for serialized_oid, counter in request.refsToUpdate.items():
                ref_counting[serialized_oid] = counter

            self.execution_environment.update_refs(ref_counting)
            return common_messages_pb2.ExceptionInfo()

        except Exception as ex:
            traceback.print_exc()
            return self.get_exception_info(ex)
      
    def getRetainedReferences(self, request, context):
        try: 

            result = self.execution_environment.get_retained_references()
            retained_refs = []

            for oid in result:
                retained_refs.append(Utils.get_msg_options['object'](oid))
            return dataservice_messages_pb2.GetRetainedReferencesResponse(retainedReferences=retained_refs)

        except Exception as ex:
            return self.get_exception_info(ex)

    def closeSessionInDS(self, request, context):
        try: 
            self.execution_environment.close_session_in_ee(Utils.get_id(request.sessionID))
            return common_messages_pb2.ExceptionInfo()

        except Exception as ex:
            return self.get_exception_info(ex)

    def migrateObjectsToBackends(self, request, context):

        try:
            backends = dict()

            for k, v in request.destStorageLocs.items():
                backends[Utils.get_id_from_uuid(k)] = dataclay_yaml_load(v)

            result = self.client.ds_migrate_objects_to_backends(backends)

            migr_obj_res = dict()

            for k, v in result[0].items():
                migrated_obj_list = list()

                for oid in v:
                    migrated_obj_list.append(Utils.get_msg_options['object'](oid))
                
                migrated_obj_builder = dataservice_messages_pb2.MigratedObjects(objs=migrated_obj_list)
                migr_obj_res[str(k)] = migrated_obj_builder

            non_migrated_objs_list = list()

            for oid in result[1]:
                non_migrated_objs_list.append(Utils.get_msg_options['object'](oid))
            
            non_migrated_objs_builder = dataservice_messages_pb2.MigratedObjects(objs=non_migrated_objs_list)

            return dataservice_messages_pb2.MigrateObjectsResponse(
                migratedObjs=migr_obj_res,
                nonMigratedObjs=non_migrated_objs_builder
            )

        except Exception as ex:
            return dataservice_messages_pb2.MigrateObjectsResponse(
                excInfo=self.get_exception_info(ex)
            )

    def activateTracing(self, request, context):
        try: 

            self.execution_environment.activate_tracing(request.taskid)
            return common_messages_pb2.ExceptionInfo()

        except Exception as ex:
            return self.get_exception_info(ex)

    def getTraces(self, request, context):
        try: 
            result = self.execution_environment.get_traces()
            return common_messages_pb2.GetTracesResponse(traces=result)
        except Exception as ex:
            return self.get_exception_info(ex)
    
    def deactivateTracing(self, request, context):
        try:
            self.execution_environment.deactivate_tracing()
            return common_messages_pb2.ExceptionInfo()

        except Exception as ex:
            return self.get_exception_info(ex)
