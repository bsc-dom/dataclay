""" Class description goes here. """

import logging
import pickle
import signal
import threading
import traceback
from concurrent import futures
from uuid import UUID

import grpc
from google.protobuf.empty_pb2 import Empty
from google.protobuf.wrappers_pb2 import BytesValue

from dataclay.backend.api import BackendAPI
from dataclay.conf import settings
from dataclay.proto.backend import backend_pb2, backend_pb2_grpc
from dataclay.proto.common import common_pb2

logger = logging.getLogger(__name__)


def serve():
    stop_event = threading.Event()

    backend = BackendAPI(
        settings.DATACLAY_BACKEND_NAME,
        settings.DATACLAY_BACKEND_PORT,
        settings.DATACLAY_KV_HOST,
        settings.DATACLAY_KV_PORT,
    )

    if not backend.is_ready(timeout=10):
        logger.error("Backend is not ready. Aborting!")
        raise

    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=settings.THREAD_POOL_WORKERS),
        options=[("grpc.max_send_message_length", -1), ("grpc.max_receive_message_length", -1)],
    )
    backend_pb2_grpc.add_BackendServiceServicer_to_server(
        BackendServicer(backend, stop_event), server
    )

    address = f"{settings.DATACLAY_LISTEN_ADDRESS}:{settings.DATACLAY_BACKEND_PORT}"
    server.add_insecure_port(address)
    server.start()

    # Autoregister of backend to MetadataService
    backend.runtime.metadata_service.register_backend(
        settings.DATACLAY_BACKEND_ID,
        settings.DATACLAY_BACKEND_HOST,
        settings.DATACLAY_BACKEND_PORT,
        settings.DATACLAY_ID,
    )

    # Set signal hook for SIGINT and SIGTERM
    signal.signal(signal.SIGINT, lambda sig, frame: stop_event.set())
    signal.signal(signal.SIGTERM, lambda sig, frame: stop_event.set())

    # Wait until stop_event is set. Then, gracefully stop dataclay backend.
    stop_event.wait()

    # TODO: Check if the order can be changed to avoid new calls when shutting down
    backend.shutdown()
    server.stop(5)


class BackendServicer(backend_pb2_grpc.BackendServiceServicer):
    def __init__(self, backend: BackendAPI, stop_event: threading.Event):
        """Execution environment being managed"""
        self.backend = backend
        self.stop_event = stop_event

    def RegisterObjects(self, request, context):
        try:
            self.backend.register_objects(request.dict_bytes, request.make_replica)
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()
        return Empty()

    def MakePersistent(self, request, context):
        try:
            self.backend.make_persistent(request.pickled_obj)
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()
        return Empty()

    def CallActiveMethod(self, request, context):
        try:
            value, is_exception = self.backend.call_active_method(
                UUID(request.session_id),
                UUID(request.object_id),
                request.method_name,
                request.args,
                request.kwargs,
            )
            return backend_pb2.CallActiveMethodResponse(value=value, is_exception=is_exception)
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return backend_pb2.CallActiveMethodResponse()

    #################
    # Store Methods #
    #################

    def GetObjectProperties(self, request, context):
        try:
            result = self.backend.get_object_properties(UUID(request.object_id))
            return BytesValue(value=result)
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return BytesValue()

    def UpdateObjectProperties(self, request, context):
        try:
            self.backend.update_object_properties(
                UUID(request.object_id), request.serialized_properties
            )
            return Empty()
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()

    def NewObjectVersion(self, request, context):
        try:
            result = self.backend.new_object_version(UUID(request.object_id))
            return backend_pb2.NewObjectVersionResponse(object_info=result)
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return backend_pb2.NewObjectVersionResponse()

    def ConsolidateObjectVersion(self, request, context):
        try:
            self.backend.consolidate_object_version(UUID(request.object_id))
            return Empty()
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()

    def ProxifyObject(self, request, context):
        try:
            self.backend.proxify_object(UUID(request.object_id), UUID(request.new_object_id))
            return Empty()
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()

    def ChangeObjectId(self, request, context):
        try:
            self.backend.change_object_id(UUID(request.object_id), UUID(request.new_object_id))
            return Empty()
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()

    def SendObjects(self, request, context):
        try:
            self.backend.send_objects(
                map(UUID, request.object_ids),
                UUID(request.backend_id),
                request.make_replica,
                request.recursive,
                request.remotes,
            )
            return Empty()
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()

    def FlushAll(self, request, context):
        try:
            self.backend.flush_all()
            return Empty()
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()

    def Shutdown(self, request, context):
        try:
            self.stop_event.set()
            return Empty()
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()

    def Drain(self, request, context):
        try:
            self.backend.move_all_objects()
            self.stop_event.set()
            return Empty()
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()

    def NewObjectReplica(self, request, context):
        try:
            self.backend.new_object_replica(
                UUID(request.object_id),
                UUID(request.backend_id),
                request.recursive,
                request.remotes,
            )
            return Empty()
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()

    ###########
    # END NEW #
    ###########

    def synchronize(self, request, context):
        raise Exception("To refactor")
        try:
            object_id = UUID(request.objectID)
            implementation_id = UUID(request.implementationID)
            serialized_params = Utils.get_param_or_return(request.params)
            session_id = UUID(request.sessionID)
            calling_backend_id = UUID(request.callingBackendID)
            self.backend.synchronize(
                session_id, object_id, implementation_id, serialized_params, calling_backend_id
            )
            return common_pb2.ExceptionInfo()
        except DataClayException as ex:
            return self.get_exception_info(ex)

    def removeObjects(self, request, context):
        raise Exception("To refactor")
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

    def updateRefs(self, request, context):
        raise Exception("To refactor")
        try:
            """deserialize into dictionary of object id - integer"""
            ref_counting = dict()
            for serialized_oid, counter in request.refsToUpdate.items():
                ref_counting[serialized_oid] = counter

            self.backend.update_refs(ref_counting)
            return common_pb2.ExceptionInfo()

        except Exception as ex:
            traceback.print_exc()
            return self.get_exception_info(ex)

    def getRetainedReferences(self, request, context):
        raise Exception("To refactor")
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
        raise Exception("To refactor")
        try:
            self.backend.close_session_in_ee(UUID(request.sessionID))
            return common_pb2.ExceptionInfo()

        except Exception as ex:
            return self.get_exception_info(ex)

    def detachObjectFromSession(self, request, context):
        raise Exception("To refactor")
        try:
            self.backend.detach_object_from_session(UUID(request.objectID), UUID(request.sessionID))
            return common_pb2.ExceptionInfo()

        except Exception as ex:
            return self.get_exception_info(ex)

    def migrateObjectsToBackends(self, request, context):
        raise Exception("To refactor")
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

    ##############
    # Federation #
    ##############

    def federate(self, request, context):
        raise Exception("To refactor")
        try:
            logger.debug("Federation started")
            self.backend.federate(
                UUID(request.sessionID),
                UUID(request.objectID),
                UUID(request.externalExecutionEnvironmentID),
                request.recursive,
            )
            logger.debug("Federation finished, sending response")
            return common_pb2.ExceptionInfo()
        except Exception as ex:
            traceback.print_exc()
            return self.get_exception_info(ex)

    def unfederate(self, request, context):
        raise Exception("To refactor")
        try:
            logger.debug("Unfederation started")
            self.backend.unfederate(
                UUID(request.sessionID),
                UUID(request.objectID),
                UUID(request.externalExecutionEnvironmentID),
                request.recursive,
            )
            logger.debug("Unfederation finished, sending response")
            return common_pb2.ExceptionInfo()
        except Exception as ex:
            return self.get_exception_info(ex)

    def notifyFederation(self, request, context):
        raise Exception("To refactor")
        try:
            logger.debug("Notify Federation started")
            objects_to_persist = []
            for vol_param in request.objects:
                param = Utils.get_obj_with_data_param_or_return(vol_param)
                objects_to_persist.append(param)
            session_id = UUID(request.sessionID)
            self.backend.notify_federation(session_id, objects_to_persist)
            logger.debug("Notify Federation finished, sending response")
            return common_pb2.ExceptionInfo()

        except Exception as ex:
            return self.get_exception_info(ex)

    def notifyUnfederation(self, request, context):
        raise Exception("To refactor")
        try:
            logger.debug("Notify Unfederation started")
            session_id = UUID(request.sessionID)
            object_ids = set()
            for oid in request.objectIDs:
                object_ids.add(UUID(oid))
            self.backend.notify_unfederation(session_id, object_ids)
            logger.debug("Notify Unfederation finished, sending response")
            return common_pb2.ExceptionInfo()

        except Exception as ex:
            traceback.print_exc()
            return self.get_exception_info(ex)

    ###########
    # Tracing #
    ###########

    def activateTracing(self, request, context):
        raise Exception("To refactor")
        try:
            self.backend.activate_tracing(request.taskid)
            return common_pb2.ExceptionInfo()

        except Exception as ex:
            return self.get_exception_info(ex)

    def getTraces(self, request, context):
        raise Exception("To refactor")
        try:
            result = self.backend.get_traces()
            return common_pb2.GetTracesResponse(traces=result)
        except Exception as ex:
            return self.get_exception_info(ex)

    def deactivateTracing(self, request, context):
        raise Exception("To refactor")
        try:
            self.backend.deactivate_tracing()
            return common_pb2.ExceptionInfo()

        except Exception as ex:
            return self.get_exception_info(ex)
