""" Class description goes here. """

"""gRPC ExecutionEnvironment Server code - StorageLocation/EE methods."""

import logging
import pickle
import traceback
from uuid import UUID

import grpc
from dataclay_common.protos import (
    common_messages_pb2,
    dataservice_messages_pb2,
    dataservice_pb2_grpc,
)
from google.protobuf.empty_pb2 import Empty
from google.protobuf.wrappers_pb2 import BytesValue

from dataclay.communication.grpc import Utils
from dataclay.exceptions.exceptions import DataClayException
from dataclay.backend.backend_api import ExecutionEnvironment
from dataclay.runtime import get_runtime

logger = logging.getLogger(__name__)


# from concurrent import futures

# from dataclay.util import Configuration
# from dataclay.runtime import settings

# max_workers = Configuration.THREAD_POOL_WORKERS or None
# address = str(settings.server_listen_addr) + ":" + str(settings.server_listen_port)


# def serve():
#     server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
#     dataservice_pb2_grpc.add_DataServiceServicer_to_server(BackendServicer(_), server)
#     server.add_insecure_port(address)
#     server.start()
#     server.wait_for_termination()


class BackendServicer(dataservice_pb2_grpc.DataServiceServicer):

    interceptor = None

    def __init__(self, theexec_env: ExecutionEnvironment, interceptor=None):
        """Execution environment being managed"""
        self.execution_environment = theexec_env
        BackendServicer.interceptor = interceptor

    def ass_client(self):
        self.client = get_runtime().backend_clients["@STORAGE"]

    def get_exception_info(self, ex):
        ex_message = None
        logger.warning("Exception produced type: %s", type(ex))
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
            exceptionMessage=Utils.prepare_exception(ex_message, Utils.return_stack()),
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

            oid = self.client.ds_new_persistent_instance(
                Utils.get_id(request.sessionID),
                Utils.get_id(request.classID),
                Utils.get_id(request.implementationID),
                iface_bit_maps,
                params,
            )

            return dataservice_messages_pb2.NewPersistentInstanceResponse(
                objectID=Utils.get_msg_id(oid)
            )

        except Exception as ex:
            return dataservice_messages_pb2.NewPersistentInstanceResponse(
                excInfo=self.get_exception_info(ex)
            )

    def storeObjects(self, request, context):

        try:
            objects_list = []
            for vol_param in request.objects:
                param = Utils.get_obj_with_data_param_or_return(vol_param)
                objects_list.append(param)

            ids_with_alias_set = set()
            session_id = Utils.get_id(request.sessionID)
            if request.idsWithAlias is not None and len(request.idsWithAlias) > 0:
                for ids_with_alias in request.idsWithAlias:
                    ids_with_alias_set.add(Utils.get_id(ids_with_alias))

            self.execution_environment.store_objects(
                session_id, objects_list, request.moving, ids_with_alias_set
            )
            return common_messages_pb2.ExceptionInfo()

        except Exception as ex:
            return self.get_exception_info(ex)

    def MakePersistent(self, request, context):
        try:
            self.execution_environment.new_make_persistent(
                UUID(request.session_id), request.pickled_obj
            )
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()
        return Empty()

    # TODO: Deprecate it, use MakePersistent
    def makePersistent(self, request, context):
        try:

            objects_to_persist = []
            for vol_param in request.objects:
                param = Utils.get_obj_with_data_param_or_return(vol_param)
                objects_to_persist.append(param)

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
            self.execution_environment.federate(
                Utils.get_id(request.sessionID),
                Utils.get_id(request.objectID),
                Utils.get_id(request.externalExecutionEnvironmentID),
                request.recursive,
            )
            logger.verbose("Federation finished, sending response")
            return common_messages_pb2.ExceptionInfo()
        except Exception as ex:
            traceback.print_exc()
            return self.get_exception_info(ex)

    def unfederate(self, request, context):
        try:
            logger.verbose("Unfederation started")
            self.execution_environment.unfederate(
                Utils.get_id(request.sessionID),
                Utils.get_id(request.objectID),
                Utils.get_id(request.externalExecutionEnvironmentID),
                request.recursive,
            )
            logger.verbose("Unfederation finished, sending response")
            return common_messages_pb2.ExceptionInfo()
        except Exception as ex:
            return self.get_exception_info(ex)

    def notifyFederation(self, request, context):
        try:
            logger.verbose("Notify Federation started")
            objects_to_persist = []
            for vol_param in request.objects:
                param = Utils.get_obj_with_data_param_or_return(vol_param)
                objects_to_persist.append(param)
            session_id = Utils.get_id(request.sessionID)
            self.execution_environment.notify_federation(session_id, objects_to_persist)
            logger.verbose("Notify Federation finished, sending response")
            return common_messages_pb2.ExceptionInfo()

        except Exception as ex:
            return self.get_exception_info(ex)

    def notifyUnfederation(self, request, context):
        try:
            logger.verbose("Notify Unfederation started")
            session_id = Utils.get_id(request.sessionID)
            object_ids = set()
            for oid in request.objectIDs:
                object_ids.add(Utils.get_id(oid))
            self.execution_environment.notify_unfederation(session_id, object_ids)
            logger.verbose("Notify Unfederation finished, sending response")
            return common_messages_pb2.ExceptionInfo()

        except Exception as ex:
            traceback.print_exc()
            return self.get_exception_info(ex)

    def CallActiveMethod(self, request, context):
        try:
            returned_value = self.execution_environment.call_active_method(
                UUID(request.session_id),
                UUID(request.object_id),
                request.method_name,
                request.args,
                request.kwargs,
            )
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return BytesValue()
        return BytesValue(value=returned_value)

    # TODO: Depreacte it. Use CallActiveMethod
    def executeImplementation(self, request, context):
        logger.debug("Starting ExecuteImplementation handling")

        try:
            object_id = Utils.get_id(request.objectID)
            implementation_id = Utils.get_id(request.implementationID)
            serialized_params = Utils.get_param_or_return(request.params)
            session_id = Utils.get_id(request.sessionID)
            result = self.execution_environment.ds_exec_impl(
                object_id, implementation_id, serialized_params, session_id
            )
            logger.verbose("ExecuteImplementation finished, sending response")

            return dataservice_messages_pb2.ExecuteImplementationResponse(
                ret=Utils.get_param_or_return(result)
            )

        except Exception as ex:
            traceback.print_exc()
            return dataservice_messages_pb2.ExecuteImplementationResponse(
                excInfo=self.get_exception_info(ex)
            )

    def synchronize(self, request, context):
        try:
            object_id = Utils.get_id(request.objectID)
            implementation_id = Utils.get_id(request.implementationID)
            serialized_params = Utils.get_param_or_return(request.params)
            session_id = Utils.get_id(request.sessionID)
            calling_backend_id = Utils.get_id(request.callingBackendID)
            self.execution_environment.synchronize(
                session_id, object_id, implementation_id, serialized_params, calling_backend_id
            )
            return common_messages_pb2.ExceptionInfo()
        except DataClayException as ex:
            return self.get_exception_info(ex)

    def getCopyOfObject(self, request, context):
        try:
            result = self.execution_environment.get_copy_of_object(
                Utils.get_id(request.sessionID), Utils.get_id(request.objectID), request.recursive
            )

            return dataservice_messages_pb2.GetCopyOfObjectResponse(
                ret=Utils.get_param_or_return(result)
            )

        except Exception as ex:
            return dataservice_messages_pb2.GetObjectsResponse(excInfo=self.get_exception_info(ex))

    def updateObject(self, request, context):
        try:

            self.execution_environment.update_object(
                Utils.get_id(request.sessionID),
                Utils.get_id(request.intoObjectID),
                Utils.get_param_or_return(request.fromObject),
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
            already_obtained_objects = set()
            for oid in request.alreadyObtainedObjects:
                already_obtained_objects.add(Utils.get_id(oid))
            result = self.execution_environment.get_objects(
                Utils.get_id(request.sessionID),
                object_ids,
                already_obtained_objects,
                request.recursive,
                Utils.get_id(request.destBackendID),
                request.updateReplicaLocs,
            )

            obj_list = []
            for entry in result:
                obj_list.append(Utils.get_obj_with_data_param_or_return(entry))

            return dataservice_messages_pb2.GetObjectsResponse(objects=obj_list)

        except Exception as ex:
            traceback.print_exc()
            return dataservice_messages_pb2.GetObjectsResponse(excInfo=self.get_exception_info(ex))

    def newVersion(self, request, context):
        try:
            version_object_id = self.execution_environment.new_version(
                Utils.get_id(request.sessionID),
                Utils.get_id(request.objectID),
                Utils.get_id(request.destBackendID),
            )

            return dataservice_messages_pb2.NewVersionResponse(
                objectID=Utils.get_msg_id(version_object_id)
            )

        except Exception as ex:
            traceback.print_exc()
            return dataservice_messages_pb2.NewVersionResponse(excInfo=self.get_exception_info(ex))

    def consolidateVersion(self, request, context):

        try:
            self.execution_environment.consolidate_version(
                Utils.get_id(request.sessionID), Utils.get_id(request.versionObjectID)
            )

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
        try:
            result = self.execution_environment.new_replica(
                Utils.get_id(request.sessionID),
                Utils.get_id(request.objectID),
                Utils.get_id(request.destBackendID),
                request.recursive,
            )
            repl_ids_list = []
            for oid in result:
                repl_ids_list.append(Utils.get_msg_id(oid))

            return dataservice_messages_pb2.NewReplicaResponse(replicatedObjects=repl_ids_list)

        except Exception as ex:
            traceback.print_exc()
            return dataservice_messages_pb2.NewReplicaResponse(excInfo=self.get_exception_info(ex))

    def moveObjects(self, request, context):

        try:
            result = self.execution_environment.move_objects(
                Utils.get_id(request.sessionID),
                Utils.get_id(request.objectID),
                Utils.get_id(request.destLocID),
                request.recursive,
            )
            mov_obj_list = []

            for oid in result:
                mov_obj_list.append(Utils.get_msg_id(oid))

            return dataservice_messages_pb2.MoveObjectsResponse(movedObjects=mov_obj_list)

        except Exception as ex:
            return dataservice_messages_pb2.MoveObjectsResponse(excInfo=self.get_exception_info(ex))

    def removeObjects(self, request, context):

        try:
            object_ids = set()

            for oid in request.getObjectsIDSList():
                object_ids.add(Utils.get_id(oid))

            result = self.client.ds_remove_objects(
                Utils.get_id(request.sessionID),
                object_ids,
                request.recursive,
                request.moving,
                Utils.get_id(request.newHint),
            )

            rem_obj = dict()

            for k, v in result.items():
                rem_obj[str(k)] = str(v)

            return dataservice_messages_pb2.RemoveObjectsResponse(removedObjects=rem_obj)

        except Exception as ex:
            return dataservice_messages_pb2.RemoveObjectsResponse(
                excInfo=self.get_exception_info(ex)
            )

    def exists(self, request, context):
        try:
            exists = self.execution_environment.exists(Utils.get_id(request.objectID))
            return dataservice_messages_pb2.ExistsResponse(exists=exists)
        except Exception as ex:
            return dataservice_messages_pb2.ExistsResponse(excInfo=self.get_exception_info(ex))

    def getNumObjectsInEE(self, request, context):
        try:
            num_objs = self.execution_environment.get_num_objects()
            return common_messages_pb2.GetNumObjectsResponse(numObjs=num_objs)
        except Exception as ex:
            return common_messages_pb2.GetNumObjectsResponse(excInfo=self.get_exception_info(ex))

    def updateRefs(self, request, context):
        try:

            """deserialize into dictionary of object id - integer"""
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
                retained_refs.append(Utils.get_msg_id(oid))
            return dataservice_messages_pb2.GetRetainedReferencesResponse(
                retainedReferences=retained_refs
            )

        except Exception as ex:
            return self.get_exception_info(ex)

    def closeSessionInDS(self, request, context):
        try:
            self.execution_environment.close_session_in_ee(Utils.get_id(request.sessionID))
            return common_messages_pb2.ExceptionInfo()

        except Exception as ex:
            return self.get_exception_info(ex)

    def detachObjectFromSession(self, request, context):
        try:
            self.execution_environment.detach_object_from_session(
                Utils.get_id(request.objectID), Utils.get_id(request.sessionID)
            )
            return common_messages_pb2.ExceptionInfo()

        except Exception as ex:
            return self.get_exception_info(ex)

    def deleteAlias(self, request, context):
        try:
            self.execution_environment.delete_alias(
                Utils.get_id(request.sessionID), Utils.get_id(request.objectID)
            )
            return common_messages_pb2.ExceptionInfo()

        except Exception as ex:
            return self.get_exception_info(ex)

    def migrateObjectsToBackends(self, request, context):

        try:
            backends = dict()

            for k, v in request.destStorageLocs.items():
                backends[Utils.get_id_from_uuid(k)] = Utils.get_storage_location(v)

            result = self.client.ds_migrate_objects_to_backends(backends)

            migr_obj_res = dict()

            for k, v in result[0].items():
                migrated_obj_list = list()

                for oid in v:
                    migrated_obj_list.append(Utils.get_msg_id(oid))

                migrated_obj_builder = dataservice_messages_pb2.MigratedObjects(
                    objs=migrated_obj_list
                )
                migr_obj_res[str(k)] = migrated_obj_builder

            non_migrated_objs_list = list()

            for oid in result[1]:
                non_migrated_objs_list.append(Utils.get_msg_id(oid))

            non_migrated_objs_builder = dataservice_messages_pb2.MigratedObjects(
                objs=non_migrated_objs_list
            )

            return dataservice_messages_pb2.MigrateObjectsResponse(
                migratedObjs=migr_obj_res, nonMigratedObjs=non_migrated_objs_builder
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
