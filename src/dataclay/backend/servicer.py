""" Class description goes here. """

import logging
import os.path
import signal
import threading
import traceback
from concurrent import futures
from uuid import UUID, uuid4

import grpc
from google.protobuf.empty_pb2 import Empty
from google.protobuf.wrappers_pb2 import BytesValue
from grpc_health.v1 import health, health_pb2, health_pb2_grpc

from dataclay.backend.api import BackendAPI
from dataclay.config import settings
from dataclay.proto.backend import backend_pb2, backend_pb2_grpc
from dataclay.proto.common import common_pb2

logger = logging.getLogger(__name__)


def _get_or_generate_backend_id() -> UUID:
    """Try to retrieve this backend UUID, or generate a new one.

    If there is no backend_id defined in the settings, try to get the
    backend UUID. A file may exist in the storage folder (which means that
    this backend already has a identifer, so we should reuse it).

    If there is no UUID in persistent storage, then this means that this is
    the first time this backend has started, so we generate a new one and
    store it.
    """
    backend_id_file = os.path.join(settings.storage_path, "BACKEND_ID")

    if settings.backend.id is None and os.path.exists(backend_id_file):
        # Seems like we will be using a preexisting UUID
        with open(backend_id_file, "rt") as f:
            ret = UUID(f.read())
            logger.info("Starting backend with recovered UUID: %s", ret)
            return ret

    if settings.backend.id is None:
        backend_id = uuid4()
        logger.info("BackendID randomly generated: %s", backend_id)
    else:
        backend_id = settings.backend.id
        logger.info("BackendID defined in settings: %s", backend_id)

    # Store the backend_id and return it
    try:
        with open(backend_id_file, "wt") as f:
            f.write(str(backend_id))
            logger.debug("BackendID has been stored in the following file: %s", backend_id_file)
    except OSError:
        logger.warning(
            "Could not write the BackendID in persistent storage. "
            "Restarting this backend may result in unreachable/unrecoverable objects."
        )
        logger.debug("Exception when trying to access persistent backend id file:", exc_info=True)
    return backend_id


def serve():
    stop_event = threading.Event()

    backend_id = _get_or_generate_backend_id()

    logger.info("Starting backend service")
    backend = BackendAPI(
        settings.backend.name,
        settings.backend.port,
        backend_id,
        settings.kv_host,
        settings.kv_port,
    )

    if not backend.is_ready(timeout=10):
        raise RuntimeError("KV store is not ready. Aborting!")

    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=settings.thread_pool_max_workers),
        options=[("grpc.max_send_message_length", -1), ("grpc.max_receive_message_length", -1)],
    )
    backend_pb2_grpc.add_BackendServiceServicer_to_server(
        BackendServicer(backend, stop_event), server
    )

    if settings.backend.enable_healthcheck:
        logger.info("Enabling healthcheck for BackendService")
        health_servicer = health.HealthServicer(
            experimental_non_blocking=True,
            experimental_thread_pool=futures.ThreadPoolExecutor(
                max_workers=settings.healthcheck_max_workers
            ),
        )
        health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)
        health_servicer.set(
            "dataclay.proto.backend.BackendService", health_pb2.HealthCheckResponse.SERVING
        )

    address = f"{settings.backend.listen_address}:{settings.backend.port}"
    server.add_insecure_port(address)
    server.start()
    logger.info("Backend service listening on %s", address)

    # Autoregister of backend to KV store
    backend.runtime.metadata_service.register_backend(
        backend_id,
        settings.backend.host,
        settings.backend.port,
        settings.dataclay_id,
    )

    # Set signal hook for SIGINT and SIGTERM
    signal.signal(signal.SIGINT, lambda sig, frame: stop_event.set())
    signal.signal(signal.SIGTERM, lambda sig, frame: stop_event.set())

    # Wait until stop_event is set. Then, gracefully stop dataclay backend.
    stop_event.wait()
    logger.info("Stopping backend service")

    # TODO: Check if the order can be changed to avoid new calls when shutting down
    backend.stop()
    server.stop(5)


class BackendServicer(backend_pb2_grpc.BackendServiceServicer):
    def __init__(self, backend: BackendAPI, stop_event: threading.Event):
        """Execution environment being managed"""
        self.backend = backend
        self.stop_event = stop_event

    def _check_backend(self, context):
        """Check if the backend-id metadata field matches this backend.

        There are scenarios in which backend-id will not be set, and that
        is not an issue. However, a mismatch is a strange scenario, which
        warrants at least an error log.
        """
        metadata = context.invocation_metadata()

        for key, value in metadata:
            if key == "backend-id":
                if value != str(self.backend.backend_id):
                    logger.error(
                        "The gRPC call was intended for backend_id=%s. We are %s. "
                        "Ignoring it and proceeding (may fail).",
                        value,
                        self.backend.backend_id,
                    )
                break
        else:
            logger.debug("No backend-id metadata header in the call.")

    def RegisterObjects(self, request, context):
        self._check_backend(context)
        try:
            self.backend.register_objects(request.dict_bytes, request.make_replica)
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()
        return Empty()

    def MakePersistent(self, request, context):
        self._check_backend(context)
        try:
            self.backend.make_persistent(request.pickled_obj)
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()
        return Empty()

    def CallActiveMethod(self, request, context):
        self._check_backend(context)
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
        self._check_backend(context)
        try:
            result = self.backend.get_object_properties(UUID(request.object_id))
            return BytesValue(value=result)
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return BytesValue()

    def UpdateObjectProperties(self, request, context):
        self._check_backend(context)
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
        self._check_backend(context)
        try:
            result = self.backend.new_object_version(UUID(request.object_id))
            return backend_pb2.NewObjectVersionResponse(object_info=result)
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return backend_pb2.NewObjectVersionResponse()

    def ConsolidateObjectVersion(self, request, context):
        self._check_backend(context)
        try:
            self.backend.consolidate_object_version(UUID(request.object_id))
            return Empty()
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()

    def ProxifyObject(self, request, context):
        self._check_backend(context)
        try:
            self.backend.proxify_object(UUID(request.object_id), UUID(request.new_object_id))
            return Empty()
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()

    def ChangeObjectId(self, request, context):
        self._check_backend(context)
        try:
            self.backend.change_object_id(UUID(request.object_id), UUID(request.new_object_id))
            return Empty()
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()

    def SendObjects(self, request, context):
        self._check_backend(context)
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
        self._check_backend(context)
        try:
            self.backend.flush_all()
            return Empty()
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()

    def Stop(self, request, context):
        self._check_backend(context)
        try:
            self.stop_event.set()
            return Empty()
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()

    def Drain(self, request, context):
        self._check_backend(context)
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
        self._check_backend(context)
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

            rem_obj = {}

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
            ref_counting = {}
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
            backends = {}

            for k, v in request.destStorageLocs.items():
                backends[UUID(k)] = Utils.get_storage_location(v)

            result = self.client.ds_migrate_objects_to_backends(backends)

            migr_obj_res = {}

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
