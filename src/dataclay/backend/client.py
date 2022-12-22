import logging
import pickle
import sys
import traceback
from uuid import UUID

import grpc
from dataclay_common.protos import common_messages_pb2 as CommonMessages
from dataclay_common.protos import (
    dataservice_messages_pb2,
    dataservice_pb2,
    dataservice_pb2_grpc,
)
from grpc._cython.cygrpc import ChannelArgKey

from dataclay.conf import settings
from dataclay.exceptions.exceptions import DataClayException
from dataclay.utils.decorators import grpc_error_handler

logger = logging.getLogger(__name__)


class BackendClient:
    def __init__(self, hostname, port):
        """Create the stub and the channel at the address passed by the server."""
        self.address = str(hostname) + ":" + str(port)
        options = [
            (ChannelArgKey.max_send_message_length, -1),
            (ChannelArgKey.max_receive_message_length, -1),
        ]
        self.metadata_call = []
        if (
            settings.SSL_CLIENT_TRUSTED_CERTIFICATES != ""
            or settings.SSL_CLIENT_CERTIFICATE != ""
            or settings.SSL_CLIENT_KEY != ""
        ):
            # read in certificates
            options.append(("grpc.ssl_target_name_override", settings.SSL_TARGET_AUTHORITY))
            if port != 443:
                service_alias = str(port)
                self.metadata_call.append(("service-alias", service_alias))
                self.address = f"{hostname}:443"
                logger.info(f"SSL configured: changed address {hostname}:{port} to {hostname}:443")
                logger.info("SSL configured: using service-alias  " + service_alias)
            else:
                self.metadata_call.append(("service-alias", settings.SSL_TARGET_EE_ALIAS))

            try:
                if settings.SSL_CLIENT_TRUSTED_CERTIFICATES != "":
                    with open(settings.SSL_CLIENT_TRUSTED_CERTIFICATES, "rb") as f:
                        trusted_certs = f.read()
                if settings.SSL_CLIENT_CERTIFICATE != "":
                    with open(settings.SSL_CLIENT_CERTIFICATE, "rb") as f:
                        client_cert = f.read()

                if settings.SSL_CLIENT_KEY != "":
                    with open(settings.SSL_CLIENT_KEY, "rb") as f:
                        client_key = f.read()
            except Exception as e:
                logger.error("failed-to-read-cert-keys", reason=e)

            # create credentials
            if trusted_certs is not None:
                credentials = grpc.ssl_channel_credentials(
                    root_certificates=trusted_certs,
                    private_key=client_key,
                    certificate_chain=client_cert,
                )
            else:
                credentials = grpc.ssl_channel_credentials(
                    private_key=client_key, certificate_chain=client_cert
                )

            self.channel = grpc.secure_channel(self.address, credentials, options)

            logger.info(
                "SSL configured: using SSL_CLIENT_TRUSTED_CERTIFICATES located at "
                + settings.SSL_CLIENT_TRUSTED_CERTIFICATES
            )
            logger.info(
                "SSL configured: using SSL_CLIENT_CERTIFICATE located at "
                + settings.SSL_CLIENT_CERTIFICATE
            )
            logger.info(
                "SSL configured: using SSL_CLIENT_KEY located at " + settings.SSL_CLIENT_KEY
            )
            logger.info("SSL configured: using authority  " + settings.SSL_TARGET_AUTHORITY)

        else:
            self.channel = grpc.insecure_channel(self.address, options)
            logger.info("SSL not configured")

        try:
            grpc.channel_ready_future(self.channel).result(
                timeout=settings.GRPC_CHECK_ALIVE_TIMEOUT
            )
        except Exception as e:
            sys.exit("Error connecting to server %s" % self.address)
        else:
            self.stub = dataservice_pb2_grpc.DataServiceStub(self.channel)

    # NOTE: It may be not need if the channel_ready_future is check on __init__
    def is_ready(self, timeout=None):
        try:
            grpc.channel_ready_future(self.channel).result(timeout)
            return True
        except grpc.FutureTimeoutError:
            return False

    def close(self):
        """Closing channel by deleting channel and stub"""
        del self.channel
        del self.stub
        self.channel = None
        self.stub = None

    # def ds_deploy_metaclasses(self, namespace_name, deployment_pack):
    #     deployment_pack_dict = dict()

    #     for k, v in deployment_pack.items():
    #         deployment_pack_dict[k] = dataclay_yaml_dump(v)

    #     request = dataservice_messages_pb2.DeployMetaClassesRequest(
    #         namespace=namespace_name, deploymentPack=deployment_pack_dict
    #     )

    #     try:
    #         response = self.stub.deployMetaClasses(request=request, metadata=self.metadata_call)

    #     except RuntimeError as e:
    #         raise e

    #     if response.isException:
    #         raise DataClayException(response.exceptionMessage)

    def ds_new_persistent_instance(
        self, session_id, class_id, implementation_id, i_face_bitmaps, params
    ):

        raise ("To refactor")
        logger.debug(
            "Ready to call to a DS to build a new persistent instance for class {%s}", class_id
        )
        temp_iface_b = dict()
        temp_param = None

        if i_face_bitmaps is not None:
            for k, v in i_face_bitmaps.items():
                temp_iface_b[k] = v

        if params is not None:
            temp_param = Utils.get_param_or_return(params)

        request = dataservice_messages_pb2.NewPersistentInstanceRequest(
            sessionID=str(session_id),
            classID=str(class_id),
            implementationID=str(implementation_id),
            ifaceBitMaps=temp_iface_b,
            params=temp_param,
        )

        try:
            response = self.stub.newPersistentInstance(request, metadata=self.metadata_call)

        except RuntimeError as e:
            raise e

        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        return UUID(response.objectID)

    def ds_store_objects(self, session_id, objects, moving, ids_with_alias):

        raise ("To Refactor")
        obj_list = []
        id_with_alias_list = []

        for obj in objects:
            obj_list.append(Utils.get_obj_with_data_param_or_return(obj))

        if ids_with_alias is not None:
            for id_with_alias in ids_with_alias:
                if id_with_alias is not None:
                    id_with_alias_list.append(str(id_with_alias))

        request = dataservice_messages_pb2.StoreObjectsRequest(
            sessionID=str(session_id),
            objects=obj_list,
            moving=moving,
            idsWithAlias=id_with_alias_list,
        )

        try:
            response = self.stub.storeObjects(request, metadata=self.metadata_call)

        except RuntimeError as e:
            traceback.print_exc(file=sys.stdout)
            raise e

        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def ds_get_copy_of_object(self, session_id, object_id, recursive):
        raise ("To refactor")
        request = dataservice_messages_pb2.GetCopyOfObjectRequest(
            sessionID=str(session_id),
            objectID=str(object_id),
            recursive=recursive,
        )

        try:
            response = self.stub.getCopyOfObject(request, metadata=self.metadata_call)

        except RuntimeError as e:
            raise e

        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        serialized_obj = Utils.get_param_or_return(response.ret)

        return serialized_obj

    def ds_update_object(self, session_id, into_object_id, from_object):
        raise ("To refactor")
        request = dataservice_messages_pb2.UpdateObjectRequest(
            sessionID=str(session_id),
            intoObjectID=str(into_object_id),
            fromObject=Utils.get_param_or_return(from_object),
        )

        try:
            response = self.stub.updateObject(request, metadata=self.metadata_call)

        except RuntimeError as e:
            raise e

        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def ds_get_objects(
        self,
        session_id,
        object_ids,
        already_obtained_obs,
        recursive,
        dest_backend_id,
        update_replica_locs,
    ):

        raise ("To refactor")
        object_ids_list = []
        for oid in object_ids:
            object_ids_list.append(str(oid))
        already_obtained_objects = []
        for oid in already_obtained_obs:
            already_obtained_objects.append(str(oid))

        request = dataservice_messages_pb2.GetObjectsRequest(
            sessionID=str(session_id),
            objectIDS=object_ids_list,
            alreadyObtainedObjects=already_obtained_objects,
            recursive=recursive,
            destBackendID=str(dest_backend_id),
            updateReplicaLocs=update_replica_locs,
        )

        try:
            response = self.stub.getObjects(request, metadata=self.metadata_call)

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
            sessionID=str(session_id),
            objectID=str(object_id),
            destBackendID=str(dest_backend_id),
        )
        try:
            response = self.stub.newVersion(request, metadata=self.metadata_call)
        except RuntimeError as e:
            raise e

        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        return UUID(response.objectID)

    def consolidate_version(self, session_id, version_object_id):
        request = dataservice_messages_pb2.ConsolidateVersionRequest(
            sessionID=str(session_id),
            versionObjectID=str(version_object_id),
        )
        try:
            response = self.stub.consolidateVersion(request, metadata=self.metadata_call)

        except RuntimeError as e:
            raise e

        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def ds_upsert_objects(self, session_id, object_bytes):

        raise ("To refactor")
        obj_byt_list = []
        for entry in object_bytes:
            obj_byt_list.append(Utils.get_obj_with_data_param_or_return(entry))

        request = dataservice_messages_pb2.UpsertObjectsRequest(
            sessionID=str(session_id), bytesUpdate=obj_byt_list
        )

        try:
            response = self.stub.upsertObjects(request, metadata=self.metadata_call)

        except RuntimeError as e:
            raise e

        if response.isException:
            raise DataClayException(response.exceptionMessage)

    @grpc_error_handler
    def make_persistent(self, session_id: UUID, pickled_obj: list[bytes]):
        request = dataservice_pb2.MakePersistentRequest(
            session_id=str(session_id), pickled_obj=pickled_obj
        )
        self.stub.MakePersistent(request)

    def federate(self, session_id, object_id, external_execution_env_id, recursive):
        try:
            request = dataservice_messages_pb2.FederateRequest(
                sessionID=str(session_id),
                objectID=str(object_id),
                externalExecutionEnvironmentID=str(external_execution_env_id),
                recursive=recursive,
            )
            response = self.stub.federate(request, metadata=self.metadata_call)
        except RuntimeError as e:
            traceback.print_exc()
            logger.error("Failed to federate", exc_info=True)
            raise e
        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def unfederate(self, session_id, object_id, external_execution_env_id, recursive):

        request = dataservice_messages_pb2.UnfederateRequest(
            sessionID=str(session_id),
            objectID=str(object_id),
            externalExecutionEnvironmentID=str(external_execution_env_id),
            recursive=recursive,
        )
        try:
            response = self.stub.unfederate(request, metadata=self.metadata_call)
        except RuntimeError as e:
            logger.error("Failed to unfederate", exc_info=True)
            raise e
        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def notify_federation(self, session_id, params):
        raise ("To refactor")
        obj_list = []
        for entry in params:
            obj_list.append(Utils.get_obj_with_data_param_or_return(entry))

        request = dataservice_messages_pb2.NotifyFederationRequest(
            sessionID=str(session_id),
            objects=obj_list,
        )

        try:
            response = self.stub.notifyFederation(request, metadata=self.metadata_call)

        except RuntimeError as e:
            logger.error("Failed to federate", exc_info=True)
            raise e

        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def notify_unfederation(self, session_id, object_ids):
        obj_list = []
        for entry in object_ids:
            obj_list.append(str(entry))

        request = dataservice_messages_pb2.NotifyUnfederationRequest(
            sessionID=str(session_id),
            objectIDs=obj_list,
        )

        try:
            response = self.stub.notifyUnfederation(request, metadata=self.metadata_call)

        except RuntimeError as e:
            logger.error("Failed to federate", exc_info=True)
            raise e

        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def call_active_method(self, session_id, object_id, method_name, args, kwargs):
        request = dataservice_pb2.CallActiveMethodRequest(
            session_id=str(session_id),
            object_id=str(object_id),
            method_name=method_name,
            args=args,
            kwargs=kwargs,
        )

        # TODO: Make it possible for the client to try..except, any possible exception from
        # the method execution.
        response = self.stub.CallActiveMethod(request)
        return response.value

    def synchronize(self, session_id, object_id, implementation_id, params, calling_backend_id):
        raise ("To refactor")
        request = dataservice_messages_pb2.SynchronizeRequest(
            sessionID=str(session_id),
            objectID=str(object_id),
            implementationID=str(implementation_id),
            params=Utils.get_param_or_return(params),
            callingBackendID=str(calling_backend_id),
        )
        try:
            response = self.stub.synchronize(request, metadata=self.metadata_call)
        except RuntimeError as e:
            raise e
        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def new_replica(self, session_id, object_id, dest_backend_id, recursive):

        request = dataservice_messages_pb2.NewReplicaRequest(
            sessionID=str(session_id),
            objectID=str(object_id),
            destBackendID=str(dest_backend_id),
            recursive=recursive,
        )

        try:
            response = self.stub.newReplica(request, metadata=self.metadata_call)

        except RuntimeError as e:
            raise e

        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        result = set()

        for oid in response.replicatedObjects:
            result.add(UUID(oid))

        return result

    def ds_move_objects(self, session_id, object_id, dest_st_location, recursive):

        request = dataservice_messages_pb2.MoveObjectsRequest(
            sessionID=str(session_id),
            objectID=str(object_id),
            destLocID=str(dest_st_location),
            recursive=recursive,
        )

        try:
            response = self.stub.moveObjects(request, metadata=self.metadata_call)

        except RuntimeError as e:
            raise e

        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        result = set()

        for oid in response.movedObjects:
            result.add(UUID(oid))

        return result

    def ds_remove_objects(self, session_id, object_ids, recursive, moving, new_hint):

        obj_ids_list = []
        for oid in object_ids:
            obj_ids_list.append(str(oid))

        request = dataservice_messages_pb2.RemoveObjectsRequest(
            sessionID=str(session_id),
            objectIDs=obj_ids_list,
            recursive=recursive,
            moving=moving,
            newHint=str(new_hint),
        )

        try:
            response = self.stub.removeObjects(request, metadata=self.metadata_call)

        except RuntimeError as e:
            raise e

        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        result = dict()

        for k, v in response.removedObjects.items():
            result[UUID(k)] = UUID(v)

        return result

    def ds_migrate_objects_to_backends(self, back_ends):

        raise ("To refactor")

        back_ends_dict = dict()

        for k, v in back_ends.items():
            back_ends_dict[k] = Utils.get_storage_location(v)

        request = dataservice_messages_pb2.MigrateObjectsRequest(destStorageLocs=back_ends_dict)

        try:
            response = self.stub.migrateObjectsToBackends(request, metadata=self.metadata_call)

        except RuntimeError as e:
            raise e

        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        result = dict()

        for k, v in response.migratedObjs.items():
            m_objs = v
            oids = set()

            for oid in m_objs.getObjsList():
                oids.add(UUID(oid))

            result[UUID(k)] = oids

        non_migrated = set()

        for oid in response.nonMigratedObjs.getObjsList():
            non_migrated.add(UUID(oid))

        t = (result, non_migrated)

        return t

    def delete_alias(self, session_id, object_id):
        request = dataservice_messages_pb2.DeleteAliasRequest(
            sessionID=str(session_id), objectID=str(object_id)
        )
        try:
            response = self.stub.deleteAlias(request, metadata=self.metadata_call)
        except RuntimeError as e:
            raise e
        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def detach_object_from_session(self, object_id, session_id):
        request = dataservice_messages_pb2.DetachObjectFromSessionRequest(
            objectID=str(object_id), sessionID=str(session_id)
        )
        try:
            response = self.stub.detachObjectFromSession(request, metadata=self.metadata_call)
        except RuntimeError as e:
            raise e
        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def activate_tracing(self, task_id):
        request = dataservice_messages_pb2.ActivateTracingRequest(taskid=task_id)

        try:
            response = self.stub.activateTracing(request, metadata=self.metadata_call)

        except RuntimeError as e:
            raise e

        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def deactivate_tracing(self):
        try:
            response = self.stub.deactivateTracing(
                CommonMessages.EmptyMessage(), metadata=self.metadata_call
            )

        except RuntimeError as e:
            raise e

        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def get_traces(self):
        try:
            response = self.stub.getTraces(
                CommonMessages.EmptyMessage(), metadata=self.metadata_call
            )
        except RuntimeError as e:
            raise e

        result = dict()
        for k, v in response.stubs.items():
            result[k] = v

        return result

    ################## EXTRAE IGNORED FUNCTIONS ###########################
    deactivate_tracing.do_not_trace = True
    activate_tracing.do_not_trace = True
