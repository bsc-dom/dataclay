""" Class description goes here. """

"""gRPC ExecutionEnvironment Server code - StorageLocation/EE methods."""

import logging
import os
import pickle
import signal
import socket
import threading
import traceback
from concurrent import futures
from uuid import UUID

import grpc
from google.protobuf.empty_pb2 import Empty
from google.protobuf.wrappers_pb2 import BytesValue

from dataclay.backend.api import BackendAPI
from dataclay.conf import settings
from dataclay.exceptions.exceptions import DataClayException
from dataclay.protos import (
    common_messages_pb2,
    dataservice_messages_pb2,
    dataservice_pb2_grpc,
)
from dataclay.protos.common_messages_pb2 import LANG_PYTHON
from dataclay.runtime import get_runtime

logger = logging.getLogger(__name__)


def serve():

    stop_event = threading.Event()

    backend = BackendAPI(
        settings.DATACLAY_BACKEND_NAME,
        settings.DATACLAY_BACKEND_PORT,
        settings.ETCD_HOSTNAME,
        settings.ETCD_PORT,
    )

    if not backend.is_ready(timeout=10):
        logger.error("Backend is not ready. Aborting!")
        raise

    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=settings.THREAD_POOL_WORKERS),
        options=[("grpc.max_send_message_length", -1), ("grpc.max_receive_message_length", -1)],
    )
    dataservice_pb2_grpc.add_DataServiceServicer_to_server(BackendServicer(backend), server)

    address = f"{settings.DATACLAY_BACKEND_LISTEN_ADDRESS}:{settings.DATACLAY_BACKEND_PORT}"
    server.add_insecure_port(address)
    server.start()

    # Autoregister of ExecutionEnvironment to MetadataService
    backend.runtime.metadata_service.autoregister_ee(
        settings.DATACLAY_BACKEND_ID,
        settings.DATACLAY_BACKEND_HOSTNAME,
        settings.DATACLAY_BACKEND_PORT,
        settings.DATACLAY_BACKEND_NAME,
        LANG_PYTHON,
    )

    # Set signal hook for SIGINT and SIGTERM
    signal.signal(signal.SIGINT, lambda sig, frame: stop_event.set())
    signal.signal(signal.SIGTERM, lambda sig, frame: stop_event.set())

    # Wait until stop_event is set. Then, gracefully stop dataclay backend.
    stop_event.wait()

    backend.stop()
    server.stop(5)


class BackendServicer(dataservice_pb2_grpc.DataServiceServicer):

    interceptor = None

    def __init__(self, backend: BackendAPI, interceptor=None):
        """Execution environment being managed"""
        self.backend = backend
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

        logger.debug("[deployMetaClasses] Deploying classes")

        try:
            namespace = request.namespace
            classes_map_yamls = request.deploymentPack
            self.backend.ds_deploy_metaclasses(namespace, classes_map_yamls)
            return common_messages_pb2.ExceptionInfo()

        except Exception as ex:
            return self.get_exception_info(ex)

    def newPersistentInstance(self, request, context):
        raise ("To refactor")

        try:
            iface_bit_maps = {}

            for k, v in request.ifaceBitMaps.items():
                iface_bit_maps[UUID(k)] = bytes(v, "utf-8")

            params = []

            if request.params:
                params = Utils.get_param_or_return(request.params)

            oid = self.client.ds_new_persistent_instance(
                UUID(request.sessionID),
                UUID(request.classID),
                UUID(request.implementationID),
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

        raise ("To refactor")
        try:
            objects_list = []
            for vol_param in request.objects:
                param = Utils.get_obj_with_data_param_or_return(vol_param)
                objects_list.append(param)

            ids_with_alias_set = set()
            session_id = UUID(request.sessionID)
            if request.idsWithAlias is not None and len(request.idsWithAlias) > 0:
                for ids_with_alias in request.idsWithAlias:
                    ids_with_alias_set.add(UUID(ids_with_alias))

            self.backend.store_objects(session_id, objects_list, request.moving, ids_with_alias_set)
            return common_messages_pb2.ExceptionInfo()

        except Exception as ex:
            return self.get_exception_info(ex)

    def MakePersistent(self, request, context):
        try:
            self.backend.make_persistent(UUID(request.session_id), list(request.pickled_obj))
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()
        return Empty()

    def federate(self, request, context):
        try:
            logger.debug("Federation started")
            self.backend.federate(
                UUID(request.sessionID),
                UUID(request.objectID),
                UUID(request.externalExecutionEnvironmentID),
                request.recursive,
            )
            logger.debug("Federation finished, sending response")
            return common_messages_pb2.ExceptionInfo()
        except Exception as ex:
            traceback.print_exc()
            return self.get_exception_info(ex)

    def unfederate(self, request, context):
        try:
            logger.debug("Unfederation started")
            self.backend.unfederate(
                UUID(request.sessionID),
                UUID(request.objectID),
                UUID(request.externalExecutionEnvironmentID),
                request.recursive,
            )
            logger.debug("Unfederation finished, sending response")
            return common_messages_pb2.ExceptionInfo()
        except Exception as ex:
            return self.get_exception_info(ex)

    def notifyFederation(self, request, context):
        try:
            logger.debug("Notify Federation started")
            objects_to_persist = []
            for vol_param in request.objects:
                param = Utils.get_obj_with_data_param_or_return(vol_param)
                objects_to_persist.append(param)
            session_id = UUID(request.sessionID)
            self.backend.notify_federation(session_id, objects_to_persist)
            logger.debug("Notify Federation finished, sending response")
            return common_messages_pb2.ExceptionInfo()

        except Exception as ex:
            return self.get_exception_info(ex)

    def notifyUnfederation(self, request, context):
        try:
            logger.debug("Notify Unfederation started")
            session_id = UUID(request.sessionID)
            object_ids = set()
            for oid in request.objectIDs:
                object_ids.add(UUID(oid))
            self.backend.notify_unfederation(session_id, object_ids)
            logger.debug("Notify Unfederation finished, sending response")
            return common_messages_pb2.ExceptionInfo()

        except Exception as ex:
            traceback.print_exc()
            return self.get_exception_info(ex)

    def CallActiveMethod(self, request, context):
        try:
            returned_value = self.backend.call_active_method(
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

    def synchronize(self, request, context):
        raise ("To refactor")
        try:
            object_id = UUID(request.objectID)
            implementation_id = UUID(request.implementationID)
            serialized_params = Utils.get_param_or_return(request.params)
            session_id = UUID(request.sessionID)
            calling_backend_id = UUID(request.callingBackendID)
            self.backend.synchronize(
                session_id, object_id, implementation_id, serialized_params, calling_backend_id
            )
            return common_messages_pb2.ExceptionInfo()
        except DataClayException as ex:
            return self.get_exception_info(ex)

    def getCopyOfObject(self, request, context):
        raise ("To refactor")
        try:
            result = self.backend.get_copy_of_object(
                UUID(request.sessionID), UUID(request.objectID), request.recursive
            )

            return dataservice_messages_pb2.GetCopyOfObjectResponse(
                ret=Utils.get_param_or_return(result)
            )

        except Exception as ex:
            return dataservice_messages_pb2.GetObjectsResponse(excInfo=self.get_exception_info(ex))

    def updateObject(self, request, context):
        raise ("To refactor")
        try:

            self.backend.update_object(
                UUID(request.sessionID),
                UUID(request.intoObjectID),
                Utils.get_param_or_return(request.fromObject),
            )

            logger.debug("updateObject finished, sending response")

            return common_messages_pb2.ExceptionInfo()

        except DataClayException as ex:
            return self.get_exception_info(ex)

    def getObjects(self, request, context):
        raise ("To refactor")
        try:
            object_ids = set()
            for oid in request.objectIDS:
                object_ids.add(UUID(oid))
            already_obtained_objects = set()
            for oid in request.alreadyObtainedObjects:
                already_obtained_objects.add(UUID(oid))
            result = self.backend.get_objects(
                UUID(request.sessionID),
                object_ids,
                already_obtained_objects,
                request.recursive,
                UUID(request.destBackendID),
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
        raise ("To refactor")
        try:
            version_object_id = self.backend.new_version(
                UUID(request.sessionID),
                UUID(request.objectID),
                UUID(request.destBackendID),
            )

            return dataservice_messages_pb2.NewVersionResponse(
                objectID=Utils.get_msg_id(version_object_id)
            )

        except Exception as ex:
            traceback.print_exc()
            return dataservice_messages_pb2.NewVersionResponse(excInfo=self.get_exception_info(ex))

    def consolidateVersion(self, request, context):

        try:
            self.backend.consolidate_version(UUID(request.sessionID), UUID(request.versionObjectID))

            return common_messages_pb2.ExceptionInfo()

        except Exception as ex:
            return self.get_exception_info(ex)

    def upsertObjects(self, request, context):

        try:
            session_id = UUID(request.sessionID)

            objects = []
            for entry in request.bytesUpdate:
                objects.append(Utils.get_obj_with_data_param_or_return(entry))

            self.backend.upsert_objects(session_id, objects)

            return common_messages_pb2.ExceptionInfo()

        except Exception as ex:
            return self.get_exception_info(ex)

    def newReplica(self, request, context):
        raise ("To refactor")
        try:
            result = self.backend.new_replica(
                UUID(request.sessionID),
                UUID(request.objectID),
                UUID(request.destBackendID),
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
            result = self.backend.move_objects(
                UUID(request.sessionID),
                UUID(request.objectID),
                UUID(request.destLocID),
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
                object_ids.add(UUID(oid))

            result = self.client.ds_remove_objects(
                UUID(request.sessionID),
                object_ids,
                request.recursive,
                request.moving,
                UUID(request.newHint),
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
            exists = self.backend.exists(UUID(request.objectID))
            return dataservice_messages_pb2.ExistsResponse(exists=exists)
        except Exception as ex:
            return dataservice_messages_pb2.ExistsResponse(excInfo=self.get_exception_info(ex))

    def getNumObjectsInEE(self, request, context):
        try:
            num_objs = self.backend.get_num_objects()
            return common_messages_pb2.GetNumObjectsResponse(numObjs=num_objs)
        except Exception as ex:
            return common_messages_pb2.GetNumObjectsResponse(excInfo=self.get_exception_info(ex))

    def updateRefs(self, request, context):
        try:

            """deserialize into dictionary of object id - integer"""
            ref_counting = dict()
            for serialized_oid, counter in request.refsToUpdate.items():
                ref_counting[serialized_oid] = counter

            self.backend.update_refs(ref_counting)
            return common_messages_pb2.ExceptionInfo()

        except Exception as ex:
            traceback.print_exc()
            return self.get_exception_info(ex)

    def getRetainedReferences(self, request, context):
        try:

            result = self.backend.get_retained_references()
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
            self.backend.close_session_in_ee(UUID(request.sessionID))
            return common_messages_pb2.ExceptionInfo()

        except Exception as ex:
            return self.get_exception_info(ex)

    def detachObjectFromSession(self, request, context):
        try:
            self.backend.detach_object_from_session(UUID(request.objectID), UUID(request.sessionID))
            return common_messages_pb2.ExceptionInfo()

        except Exception as ex:
            return self.get_exception_info(ex)

    def deleteAlias(self, request, context):
        try:
            self.backend.delete_alias(UUID(request.sessionID), UUID(request.objectID))
            return common_messages_pb2.ExceptionInfo()

        except Exception as ex:
            return self.get_exception_info(ex)

    def migrateObjectsToBackends(self, request, context):

        try:
            backends = dict()

            for k, v in request.destStorageLocs.items():
                backends[UUID(k)] = Utils.get_storage_location(v)

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

            self.backend.activate_tracing(request.taskid)
            return common_messages_pb2.ExceptionInfo()

        except Exception as ex:
            return self.get_exception_info(ex)

    def getTraces(self, request, context):
        try:
            result = self.backend.get_traces()
            return common_messages_pb2.GetTracesResponse(traces=result)
        except Exception as ex:
            return self.get_exception_info(ex)

    def deactivateTracing(self, request, context):
        try:
            self.backend.deactivate_tracing()
            return common_messages_pb2.ExceptionInfo()

        except Exception as ex:
            return self.get_exception_info(ex)
