
""" Class description goes here. """

"""gRPC ExecutionEnvironment Client code - StorageLocation/EE methods."""

import logging
import sys
import traceback
import six
import grpc

if six.PY2:
    import cPickle as pickle
elif six.PY3:
    import _pickle as pickle

from grpc._cython.cygrpc import ChannelArgKey
from dataclay.commonruntime.Settings import settings
from dataclay.communication.grpc import Utils
from dataclay.communication.grpc.generated.dataservice import dataservice_pb2_grpc
from dataclay.communication.grpc.messages.dataservice import dataservice_messages_pb2
from dataclay.exceptions.exceptions import DataClayException
from dataclay.util.YamlParser import dataclay_yaml_dump
import dataclay.communication.grpc.messages.common.common_messages_pb2 as CommonMessages
from dataclay.util import Configuration

__author__ = 'Enrico La Sala <enrico.lasala@bsc.es>'
__copyright__ = '2017 Barcelona Supercomputing Center (BSC-CNS)'

logger = logging.getLogger(__name__)


class EEClient(object):

    def __init__(self, hostname, port):
        """Create the stub and the channel at the address passed by the server."""
        self.address = str(hostname) + ":" + str(port)
        options = [(ChannelArgKey.max_send_message_length, -1),
                   (ChannelArgKey.max_receive_message_length, -1)]

        self.channel = grpc.insecure_channel(self.address, options)
        try:
            grpc.channel_ready_future(self.channel).result(timeout=Configuration.GRPC_CHECK_ALIVE_TIMEOUT)
        except Exception as e:
            sys.exit('Error connecting to server %s' % self.address)
        else:
            self.ds_stub = dataservice_pb2_grpc.DataServiceStub(self.channel)

    def close(self):
        """Closing channel by deleting channel and stub"""
        del self.channel
        del self.ds_stub
        self.channel = None
        self.ds_stub = None

    def ds_deploy_metaclasses(self, namespace_name, deployment_pack):
        deployment_pack_dict = dict()

        for k, v in deployment_pack.items():
            deployment_pack_dict[k] = dataclay_yaml_dump(v)

        request = dataservice_messages_pb2.DeployMetaClassesRequest(
            namespace=namespace_name,
            deploymentPack=deployment_pack_dict
        )

        try:
            response = self.ds_stub.deployMetaClasses(request)

        except RuntimeError as e:
            raise e

        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def ds_new_persistent_instance(self, session_id, class_id, implementation_id, i_face_bitmaps, params):

        logger.debug("Ready to call to a DS to build a new persistent instance for class {%s}",
                     class_id)
        temp_iface_b = dict()
        temp_param = None

        if i_face_bitmaps is not None:
            for k, v in i_face_bitmaps.items():
                temp_iface_b[k] = v

        if params is not None:
            temp_param = Utils.get_param_or_return(params)

        request = dataservice_messages_pb2.NewPersistentInstanceRequest(
            sessionID=Utils.get_msg_id(session_id),
            classID=Utils.get_msg_id(class_id),
            implementationID=Utils.get_msg_id(implementation_id),
            ifaceBitMaps=temp_iface_b,
            params=temp_param
        )

        try:
            response = self.ds_stub.newPersistentInstance(request)

        except RuntimeError as e:
            raise e

        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        return Utils.get_id(response.objectID)
    
    def ds_store_objects(self, session_id, objects, moving, ids_with_alias):

        obj_list = []
        id_with_alias_list = []

        for obj in objects:
            obj_list.append(Utils.get_obj_with_data_param_or_return(obj))

        if ids_with_alias is not None:
            for id_with_alias in ids_with_alias:
                if id_with_alias is not None:
                    id_with_alias_list.append(Utils.get_msg_id(id_with_alias))

        request = dataservice_messages_pb2.StoreObjectsRequest(
            sessionID=Utils.get_msg_id(session_id),
            objects=obj_list,
            moving=moving,
            idsWithAlias=id_with_alias_list
        )

        try:
            response = self.ds_stub.storeObjects(request)

        except RuntimeError as e:
            traceback.print_exc(file=sys.stdout)
            raise e

        if response.isException:
            raise DataClayException(response.exceptionMessage)


    def ds_get_copy_of_object(self, session_id, object_id, recursive):
        request = dataservice_messages_pb2.GetCopyOfObjectRequest(
            sessionID=Utils.get_msg_id(session_id),
            objectID=Utils.get_msg_id(object_id),
            recursive=recursive,
        )
        
        try:
            response = self.ds_stub.getCopyOfObject(request)

        except RuntimeError as e:
            raise e

        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)
        
        serialized_obj = Utils.get_param_or_return(response.ret)
        
        return serialized_obj
        
    def ds_update_object(self, session_id, into_object_id, from_object):
        request = dataservice_messages_pb2.UpdateObjectRequest(
            sessionID=Utils.get_msg_id(session_id),
            intoObjectID=Utils.get_msg_id(into_object_id),
            fromObject=Utils.get_param_or_return(from_object)
        )
        
        try:
            response = self.ds_stub.updateObject(request)

        except RuntimeError as e:
            raise e

        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def ds_get_objects(self, session_id, object_ids, recursive, dest_backend_id):

        object_ids_list = []
        for oid in object_ids:
            object_ids_list.append(Utils.get_msg_id(oid))

        request = dataservice_messages_pb2.GetObjectsRequest(
            sessionID=Utils.get_msg_id(session_id),
            objectIDS=object_ids_list,
            recursive=recursive,
            destBackendID=Utils.get_msg_id(dest_backend_id)
        )

        try:
            response = self.ds_stub.getObjects(request)

        except RuntimeError as e:
            raise e

        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)
        
        serialized_objs = list() 
        for obj_with_data in response.objects:
            serialized_objs.append(Utils.get_obj_with_data_param_or_return(obj_with_data))
        
        return serialized_objs

    def new_version(self, session_id, object_id, dest_backend_id):
        request = dataservice_messages_pb2.NewVersionRequest(
            sessionID=Utils.get_msg_id(session_id),
            objectID=Utils.get_msg_id(object_id),
            destBackendID=Utils.get_msg_id(dest_backend_id)
        )
        try:
            response = self.ds_stub.newVersion(request)
        except RuntimeError as e:
            raise e

        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        return Utils.get_id(response.objectID)


    def consolidate_version(self, session_id, version_object_id):
        request = dataservice_messages_pb2.ConsolidateVersionRequest(
            sessionID=Utils.get_msg_id(session_id),
            versionObjectID=Utils.get_msg_id(version_object_id),
        )
        try:
            response = self.ds_stub.consolidateVersion(request)

        except RuntimeError as e:
            raise e

        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def ds_upsert_objects(self, session_id, object_bytes):

        obj_byt_list = []
        for entry in object_bytes:
            obj_byt_list.append(Utils.get_obj_with_data_param_or_return(entry))

        request = dataservice_messages_pb2.UpsertObjectsRequest(
                sessionID=Utils.get_msg_id(session_id),
                bytesUpdate=obj_byt_list)

        try:
            response = self.ds_stub.upsertObjects(request)

        except RuntimeError as e:
            raise e

        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def make_persistent(self, session_id, params):
        logger.debug("Client performing MakePersistent")
        obj_list = []
        for entry in params:
            obj_list.append(Utils.get_obj_with_data_param_or_return(entry))

        request = dataservice_messages_pb2.MakePersistentRequest(
            sessionID=Utils.get_msg_id(session_id),
            objects=obj_list,
        )

        try:
            response = self.ds_stub.makePersistent(request)

        except RuntimeError as e:
            logger.error('Failed to make persistent', exc_info=True)
            raise e

        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def federate(self, session_id, object_id, external_execution_env_id, recursive):
        try:
            request = dataservice_messages_pb2.FederateRequest(
                sessionID=Utils.get_msg_id(session_id),
                objectID=Utils.get_msg_id(object_id),
                externalExecutionEnvironmentID=Utils.get_msg_id(external_execution_env_id),
                recursive=recursive
            )
            response = self.ds_stub.federate(request)
        except RuntimeError as e:
            traceback.print_exc()
            logger.error('Failed to federate', exc_info=True)
            raise e
        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def unfederate(self, session_id, object_id, external_execution_env_id, recursive):

        request = dataservice_messages_pb2.UnfederateRequest(
            sessionID=Utils.get_msg_id(session_id),
            objectID=Utils.get_msg_id(object_id),
            externalExecutionEnvironmentID=Utils.get_msg_id(external_execution_env_id),
            recursive=recursive
        )
        try:
            response = self.ds_stub.unfederate(request)
        except RuntimeError as e:
            logger.error('Failed to unfederate', exc_info=True)
            raise e
        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def notify_federation(self, session_id, params):
        obj_list = []
        for entry in params:
            obj_list.append(Utils.get_obj_with_data_param_or_return(entry))

        request = dataservice_messages_pb2.NotifyFederationRequest(
            sessionID=Utils.get_msg_id(session_id),
            objects=obj_list,
        )

        try:
            response = self.ds_stub.notifyFederation(request)

        except RuntimeError as e:
            logger.error('Failed to federate', exc_info=True)
            raise e

        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def notify_unfederation(self, session_id, object_ids):
        obj_list = []
        for entry in object_ids:
            obj_list.append(Utils.get_msg_id(entry))

        request = dataservice_messages_pb2.NotifyUnfederationRequest(
            sessionID=Utils.get_msg_id(session_id),
            objectIDs=obj_list,
        )

        try:
            response = self.ds_stub.notifyUnfederation(request)

        except RuntimeError as e:
            logger.error('Failed to federate', exc_info=True)
            raise e

        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def ds_execute_implementation(self, object_id, implementation_id, session_id, params):
        logger.debug("Client performing ExecuteImplementation")

        request = dataservice_messages_pb2.ExecuteImplementationRequest(
            sessionID=Utils.get_msg_id(session_id),
            implementationID=Utils.get_msg_id(implementation_id),
            params=Utils.get_param_or_return(params),
            objectID=Utils.get_msg_id(object_id)
        )

        try:
            response = self.ds_stub.executeImplementation(request)

        except RuntimeError as e:
            logger.error('Failed to execute implementation', exc_info=True)
            raise e

        if response.excInfo.isException:
            try:
                exception = pickle.loads(response.excInfo.serializedException)
            except:
                raise DataClayException(response.excInfo.exceptionMessage)
            else:
                raise exception

        if response.ret is not None:
            return Utils.get_param_or_return(response.ret)
        else:
            return None

    def synchronize(self, session_id, object_id, implementation_id, params, calling_backend_id):
        request = dataservice_messages_pb2.SynchronizeRequest(
            sessionID=Utils.get_msg_id(session_id),
            objectID=Utils.get_msg_id(object_id),
            implementationID=Utils.get_msg_id(implementation_id),
            params=Utils.get_param_or_return(params),
            callingBackendID=Utils.get_msg_id(calling_backend_id)
        )
        try:
            response = self.ds_stub.synchronize(request)
        except RuntimeError as e:
            raise e
        if response.isException:
            raise DataClayException(response.exceptionMessage)
        
    def new_replica(self, session_id, object_id, dest_backend_id, recursive):

        request = dataservice_messages_pb2.NewReplicaRequest(
            sessionID=Utils.get_msg_id(session_id),
            objectID=Utils.get_msg_id(object_id),
            destBackendID=Utils.get_msg_id(dest_backend_id),
            recursive=recursive
        )

        try:
            response = self.ds_stub.newReplica(request)

        except RuntimeError as e:
            raise e

        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        result = set()

        for oid in response.replicatedObjects:
            result.add(Utils.get_id(oid))

        return result

    def ds_move_objects(self, session_id, object_id, dest_st_location, recursive):

        request = dataservice_messages_pb2.MoveObjectsRequest(
            sessionID=Utils.get_msg_id(session_id),
            objectID=Utils.get_msg_id(object_id),
            destLocID=Utils.get_msg_id(dest_st_location),
            recursive=recursive
        )

        try:
            response = self.ds_stub.moveObjects(request)

        except RuntimeError as e:
            raise e

        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        result = set()

        for oid in response.movedObjects:
            result.add(Utils.get_id(oid))

        return result

    def ds_remove_objects(self, session_id, object_ids, recursive, moving, new_hint):

        obj_ids_list = []
        for oid in object_ids:
            obj_ids_list.append(Utils.get_msg_id(oid))

        request = dataservice_messages_pb2.RemoveObjectsRequest(
            sessionID=Utils.get_msg_id(session_id),
            objectIDs=obj_ids_list,
            recursive=recursive,
            moving=moving,
            newHint=Utils.get_msg_id(new_hint)
        )

        try:
            response = self.ds_stub.removeObjects(request)

        except RuntimeError as e:
            raise e

        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        result = dict()

        for k, v in response.removedObjects.items():
            result[Utils.get_idd(k)] = Utils.get_id(v)

        return result

    def ds_migrate_objects_to_backends(self, back_ends):

        back_ends_dict = dict()

        for k, v in back_ends.items():
            back_ends_dict[k] = Utils.get_storage_location(v)

        request = dataservice_messages_pb2.MigrateObjectsRequest(
            destStorageLocs=back_ends_dict
        )

        try:
            response = self.ds_stub.migrateObjectsToBackends(request)

        except RuntimeError as e:
            raise e

        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        result = dict()

        for k, v in response.migratedObjs.items():
            m_objs = v
            oids = set()

            for oid in m_objs.getObjsList():
                oids.add(Utils.get_id(oid))

            result[Utils.get_id(k)] = oids

        non_migrated = set()

        for oid in response.nonMigratedObjs.getObjsList():
            non_migrated.add(Utils.get_id(oid))

        t = (result, non_migrated)

        return t
    
    # STORAGE LOCATION - DBHANDLER

    def update_refs(self, ref_counting):
        
        """ ref_counting is a dict uuid - integer """ 
        request = dataservice_messages_pb2.UpdateRefsRequest(
            refsToUpdate=ref_counting
        )

        try:
            response = self.ds_stub.updateRefs(request)
        
        except RuntimeError as e:
            raise e
        
        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def store_to_db(self, execution_environment_id, object_id, obj_bytes):
        
        request = dataservice_messages_pb2.StoreToDBRequest(
            executionEnvironmentID=Utils.get_msg_id(execution_environment_id),
            objectID=Utils.get_msg_id(object_id),
            objBytes=obj_bytes
        )

        try:
            response = self.ds_stub.storeToDB(request)
        
        except RuntimeError as e:
            raise e
        
        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def get_from_db(self, execution_environment_id, object_id):

        request = dataservice_messages_pb2.GetFromDBRequest(
            executionEnvironmentID=Utils.get_msg_id(execution_environment_id),
            objectID=Utils.get_msg_id(object_id),
        )
        try:
            response = self.ds_stub.getFromDB(request)

        except RuntimeError as e:
            raise e

        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        return response.objBytes
    
    def update_to_db(self, execution_environment_id, object_id, new_obj_bytes, dirty):
        request = dataservice_messages_pb2.UpdateToDBRequest(
            executionEnvironmentID=Utils.get_msg_id(execution_environment_id),
            objectID=Utils.get_msg_id(object_id),
            objBytes=new_obj_bytes,
            dirty=dirty
        )

        try:
            response = self.ds_stub.updateToDB(request)
        
        except RuntimeError as e:
            raise e
        
        if response.isException:
            raise DataClayException(response.exceptionMessage)
    
    def delete_to_db(self, execution_environment_id, object_id):
        request = dataservice_messages_pb2.DeleteToDBRequest(
            executionEnvironmentID=Utils.get_msg_id(execution_environment_id),
            objectID=Utils.get_msg_id(object_id),
        )

        try:
            response = self.ds_stub.deleteToDB(request)
        
        except RuntimeError as e:
            raise e
        
        if response.isException:
            raise DataClayException(response.exceptionMessage)
        
    def associate_execution_environment(self, execution_environment_id):
        request = dataservice_messages_pb2.AssociateExecutionEnvironmentRequest(
            executionEnvironmentID=Utils.get_msg_id(execution_environment_id)
        )

        try:
            response = self.ds_stub.associateExecutionEnvironment(request)
        
        except RuntimeError as e:
            raise e
        
        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def activate_tracing(self, task_id):
        request = dataservice_messages_pb2.ActivateTracingRequest(
            taskid=task_id
        )
        
        try:
            response = self.ds_stub.activateTracing(request)
        
        except RuntimeError as e:
            raise e
        
        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def deactivate_tracing(self):
        try:
            response = self.ds_stub.deactivateTracing(CommonMessages.EmptyMessage())
        
        except RuntimeError as e:
            raise e
        
        if response.isException:
            raise DataClayException(response.exceptionMessage)
        
    def get_traces(self):
        try:
            response = self.ds_stub.getTraces(CommonMessages.EmptyMessage())
        except RuntimeError as e:
            raise e
        
        result = dict()
        for k, v in response.stubs.items():
            result[k] = v

        return result
        
    ################## EXTRAE IGNORED FUNCTIONS ###########################
    deactivate_tracing.do_not_trace = True
    activate_tracing.do_not_trace = True
