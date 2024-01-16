import logging
import sys
import traceback
from typing import Iterable, Optional
from uuid import UUID

import grpc
from google.protobuf.empty_pb2 import Empty
from grpc._cython.cygrpc import ChannelArgKey

import dataclay
from dataclay.config import settings
from dataclay.exceptions.exceptions import DataClayException
from dataclay.proto.backend import backend_pb2, backend_pb2_grpc
from dataclay.proto.common import common_pb2
from dataclay.utils.decorators import grpc_error_handler

logger = logging.getLogger(__name__)


class BackendClient:
    def __init__(self, host: str, port: int, backend_id: Optional[UUID] = None):
        """Create the stub and the channel at the address passed by the server.

        Optionally, the BackendID will be included in the metadata. It is not
        strictly needed, but it can be beneficial for sanity checking and also
        it is used for reverse proxy configurations.
        """
        self.host = host
        self.port = port
        self.address = str(host) + ":" + str(port)
        options = [
            (ChannelArgKey.max_send_message_length, -1),
            (ChannelArgKey.max_receive_message_length, -1),
        ]
        self.metadata_call = [("client-version", dataclay.__version__)]

        if backend_id:
            self.metadata_call.append(("backend-id", str(backend_id)))

        if (
            settings.ssl_client_trusted_certificates != ""
            or settings.ssl_client_certificate != ""
            or settings.ssl_client_key != ""
        ):
            self._configure_ssl(options)
        else:
            self.channel = grpc.insecure_channel(self.address, options)
            logger.info("SSL not configured")

        grpc.channel_ready_future(self.channel).result(timeout=settings.grpc_check_alive_timeout)
        self.stub = backend_pb2_grpc.BackendServiceStub(self.channel)

    def _configure_ssl(self, options):
        # read in certificates
        options.append(("grpc.ssl_target_name_override", settings.ssl_target_authority))
        if self.port != 443:
            service_alias = str(self.port)
            self.metadata_call.append(("service-alias", service_alias))
            self.address = f"{self.host}:443"
            logger.info(
                "SSL configured: changed address %s:%s to %s:443", self.host, self.port, self.host
            )
            logger.info("SSL configured: using service-alias %s", service_alias)
        else:
            self.metadata_call.append(("service-alias", settings.ssl_target_ee_alias))

        try:
            if settings.ssl_client_trusted_certificates != "":
                with open(settings.ssl_client_trusted_certificates, "rb") as f:
                    trusted_certs = f.read()
            if settings.ssl_client_certificate != "":
                with open(settings.ssl_client_certificate, "rb") as f:
                    client_cert = f.read()

            if settings.ssl_client_key != "":
                with open(settings.ssl_client_key, "rb") as f:
                    client_key = f.read()
        except IOError:
            logger.error(
                "Not using client trusted certificates because I was unable to read cert keys",
                exc_info=True,
            )

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
            "SSL configured: using SSL_CLIENT_TRUSTED_CERTIFICATES located at %s",
            settings.ssl_client_trusted_certificates,
        )
        logger.info(
            "SSL configured: using SSL_CLIENT_CERTIFICATE located at %s",
            settings.ssl_client_certificate,
        )
        logger.info("SSL configured: using SSL_CLIENT_KEY located at %s", settings.ssl_client_key)
        logger.info("SSL configured: using authority %s", settings.ssl_target_authority)

    # NOTE: It may not be necessary if the channel_ready_future is check on __init__
    def is_ready(self, timeout: Optional[float] = None):
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

    @grpc_error_handler
    def register_objects(self, dict_bytes: Iterable[bytes], make_replica: bool):
        request = backend_pb2.RegisterObjectsRequest(
            dict_bytes=dict_bytes, make_replica=make_replica
        )
        self.stub.RegisterObjects(request, metadata=self.metadata_call)

    @grpc_error_handler
    def make_persistent(self, pickled_obj: Iterable[bytes]):
        request = backend_pb2.MakePersistentRequest(pickled_obj=pickled_obj)
        self.stub.MakePersistent(request, metadata=self.metadata_call)

    @grpc_error_handler
    def call_active_method(
        self, session_id: UUID, object_id: UUID, method_name: str, args: bytes, kwargs: bytes
    ) -> tuple[bytes, bool]:
        request = backend_pb2.CallActiveMethodRequest(
            session_id=str(session_id),
            object_id=str(object_id),
            method_name=method_name,
            args=args,
            kwargs=kwargs,
        )

        response = self.stub.CallActiveMethod(request, metadata=self.metadata_call)
        return response.value, response.is_exception

    #################
    # Store Methods #
    #################

    @grpc_error_handler
    def get_object_attribute(self, object_id: UUID, attribute: str) -> bytes:
        request = backend_pb2.GetObjectAttributeRequest(
            object_id=str(object_id),
            attribute=attribute,
        )
        response = self.stub.GetObjectAttribute(request, metadata=self.metadata_call)
        return response.value, False
    

    @grpc_error_handler
    def set_object_attribute(self, object_id: UUID, attribute: str ,serialized_attribute: bytes):
        logger.info(serialized_attribute)
        request = backend_pb2.SetObjectAttributeRequest(
            object_id=str(object_id),
            attribute=attribute,
            serialized_attribute=serialized_attribute,
        )
        self.stub.SetObjectAttribute(request, metadata=self.metadata_call)

    @grpc_error_handler
    def get_object_properties(self, object_id: UUID) -> bytes:
        request = backend_pb2.GetObjectPropertiesRequest(
            object_id=str(object_id),
        )

        response = self.stub.GetObjectProperties(request, metadata=self.metadata_call)
        return response.value

    @grpc_error_handler
    def update_object_properties(self, object_id: UUID, serialized_properties: bytes):
        request = backend_pb2.UpdateObjectPropertiesRequest(
            object_id=str(object_id),
            serialized_properties=serialized_properties,
        )
        self.stub.UpdateObjectProperties(request, metadata=self.metadata_call)

    @grpc_error_handler
    def new_object_version(self, object_id: UUID) -> str:
        request = backend_pb2.NewObjectVersionRequest(
            object_id=str(object_id),
        )
        response = self.stub.NewObjectVersion(request, metadata=self.metadata_call)
        return response.object_info

    @grpc_error_handler
    def consolidate_object_version(self, object_id: UUID):
        request = backend_pb2.ConsolidateObjectVersionRequest(
            object_id=str(object_id),
        )
        self.stub.ConsolidateObjectVersion(request, metadata=self.metadata_call)

    @grpc_error_handler
    def proxify_object(self, object_id: UUID, new_object_id: UUID):
        request = backend_pb2.ProxifyObjectRequest(
            object_id=str(object_id),
            new_object_id=str(new_object_id),
        )
        self.stub.ProxifyObject(request, metadata=self.metadata_call)

    @grpc_error_handler
    def change_object_id(self, object_id: UUID, new_object_id: UUID):
        request = backend_pb2.ChangeObjectIdRequest(
            object_id=str(object_id),
            new_object_id=str(new_object_id),
        )
        self.stub.ChangeObjectId(request, metadata=self.metadata_call)

    @grpc_error_handler
    def send_objects(
        self,
        object_ids: Iterable[UUID],
        backend_id: UUID,
        make_replica: bool,
        recursive: bool,
        remotes: bool,
    ):
        request = backend_pb2.SendObjectsRequest(
            object_ids=map(str, object_ids),
            backend_id=str(backend_id),
            make_replica=make_replica,
            recursive=recursive,
            remotes=remotes,
        )
        self.stub.SendObjects(request, metadata=self.metadata_call)

    @grpc_error_handler
    def flush_all(self):
        self.stub.FlushAll(Empty())

    @grpc_error_handler
    def stop(self):
        self.stub.Stop(Empty())

    @grpc_error_handler
    def drain(self):
        self.stub.Drain(Empty())

    # @grpc_error_handler
    # def new_object_replica(self, object_id: UUID, backend_id: UUID, recursive: bool, remotes: bool):
    #     request = backend_pb2.NewObjectReplicaRequest(
    #         object_id=str(object_id),
    #         backend_id=str(backend_id),
    #         recursive=recursive,
    #         remotes=remotes,
    #     )
    #     self.stub.NewObjectReplica(request, metadata=self.metadata_call)

    ###########
    # END NEW #
    ###########

    def federate(self, session_id, object_id, external_execution_env_id, recursive):
        raise Exception("To refactor")
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
        raise Exception("To refactor")
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
        raise Exception("To refactor")
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
        raise Exception("To refactor")
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

    def synchronize(self, session_id, object_id, implementation_id, params, calling_backend_id):
        raise Exception("To refactor")
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

    def ds_migrate_objects_to_backends(self, back_ends):
        raise ("To refactor")

        back_ends_dict = {}

        for k, v in back_ends.items():
            back_ends_dict[k] = Utils.get_storage_location(v)

        request = dataservice_messages_pb2.MigrateObjectsRequest(destStorageLocs=back_ends_dict)

        try:
            response = self.stub.migrateObjectsToBackends(request, metadata=self.metadata_call)

        except RuntimeError as e:
            raise e

        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        result = {}

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

    def detach_object_from_session(self, object_id, session_id):
        raise Exception("To refactor")
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
        raise Exception("To refactor")
        request = dataservice_messages_pb2.ActivateTracingRequest(taskid=task_id)

        try:
            response = self.stub.activateTracing(request, metadata=self.metadata_call)

        except RuntimeError as e:
            raise e

        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def deactivate_tracing(self):
        raise Exception("To refactor")
        try:
            response = self.stub.deactivateTracing(
                common_pb2.EmptyMessage(), metadata=self.metadata_call
            )

        except RuntimeError as e:
            raise e

        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def get_traces(self):
        raise Exception("To refactor")
        try:
            response = self.stub.getTraces(common_pb2.EmptyMessage(), metadata=self.metadata_call)
        except RuntimeError as e:
            raise e

        result = {}
        for k, v in response.stubs.items():
            result[k] = v

        return result

    ################## EXTRAE IGNORED FUNCTIONS ###########################
    # deactivate_tracing.do_not_trace = True
    # activate_tracing.do_not_trace = True
