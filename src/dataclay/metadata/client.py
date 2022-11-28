import atexit
import logging
from uuid import UUID

import grpc
from dataclay_common.protos import (
    common_messages_pb2,
    metadata_service_pb2,
    metadata_service_pb2_grpc,
)
from google.protobuf.empty_pb2 import Empty

from dataclay.utils.decorators import grpc_error_handler
from dataclay.metadata.managers.dataclay import ExecutionEnvironment
from dataclay.metadata.managers.object import ObjectMetadata
from dataclay.metadata.managers.session import Session

logger = logging.getLogger(__name__)


class MetadataClient:
    def __init__(self, hostname, port):
        self.address = f"{hostname}:{port}"
        self.channel = grpc.insecure_channel(self.address)
        self.stub = metadata_service_pb2_grpc.MetadataServiceStub(self.channel)
        atexit.register(self.close)

    def is_ready(self, timeout=None):
        try:
            grpc.channel_ready_future(self.channel).result(timeout)
        except grpc.FutureTimeoutError:
            return False
        else:
            return True

    def close(self):
        self.channel.close()

    ###################
    # Session Manager #
    ###################

    @grpc_error_handler
    def new_session(self, username: str, password: str, dataset_name: str) -> Session:
        request = metadata_service_pb2.NewSessionRequest(
            username=username, password=password, dataset_name=dataset_name
        )
        response = self.stub.NewSession(request)
        return Session.from_proto(response)

    @grpc_error_handler
    def close_session(self, session_id: UUID):
        request = metadata_service_pb2.CloseSessionRequest(id=str(session_id))
        self.stub.CloseSession(request)

    ###################
    # Account Manager #
    ###################

    @grpc_error_handler
    def new_account(self, username: str, password: str):
        request = metadata_service_pb2.NewAccountRequest(username=username, password=password)
        self.stub.NewAccount(request)

    ###################
    # Dataset Manager #
    ###################

    @grpc_error_handler
    def new_dataset(self, username: str, password: str, dataset: str):
        request = metadata_service_pb2.NewDatasetRequest(
            username=username, password=password, dataset=dataset
        )
        self.stub.NewDataset(request)

    #####################
    # Dataclay Metadata #
    #####################

    @grpc_error_handler
    def get_dataclay_id(self) -> UUID:
        response = self.stub.GetDataclayID(Empty())
        return UUID(response.dataclay_id)

    #####################
    # EE-SL information #
    #####################

    @grpc_error_handler
    def get_all_execution_environments(
        self, language: int, get_external=True, from_backend=False
    ) -> dict:
        request = metadata_service_pb2.GetAllExecutionEnvironmentsRequest(
            language=language, get_external=get_external, from_backend=from_backend
        )
        response = self.stub.GetAllExecutionEnvironments(request)

        result = dict()
        for id, proto in response.exec_envs.items():
            result[UUID(id)] = ExecutionEnvironment.from_proto(proto)
        return result

    @grpc_error_handler
    def autoregister_ee(self, id: UUID, hostname: str, port: int, sl_name: str, lang: int):
        request = metadata_service_pb2.AutoRegisterEERequest(
            id=str(id), hostname=hostname, port=port, sl_name=sl_name, lang=lang
        )
        self.stub.AutoregisterEE(request)

    ###################
    # Object Metadata #
    ###################

    # TODO: Check if used
    def register_object(self, object_md: ObjectMetadata, session_id: UUID):
        request = metadata_service_pb2.RegisterObjectRequest(
            session_id=str(session_id), object_md=object_md.get_proto()
        )
        self.stub.RegisterObject(request)

    # TODO: Check if used
    def get_object_md_by_id(self, object_id: UUID, session_id: UUID) -> ObjectMetadata:
        request = metadata_service_pb2.GetObjectMDByIdRequest(
            session_id=str(session_id), object_id=str(object_id)
        )
        object_md_proto = self.stub.GetObjectMDById(request)
        return ObjectMetadata.from_proto(object_md_proto)

    @grpc_error_handler
    def get_object_md_by_alias(
        self, alias_name: str, dataset_name: str, session_id: UUID
    ) -> ObjectMetadata:
        request = metadata_service_pb2.GetObjectMDByAliasRequest(
            session_id=str(session_id), alias_name=alias_name, dataset_name=dataset_name
        )
        object_md_proto = self.stub.GetObjectMDByAlias(request)
        return ObjectMetadata.from_proto(object_md_proto)

    @grpc_error_handler
    def delete_alias(self, alias_name: str, dataset_name: str, session_id: UUID):
        request = metadata_service_pb2.DeleteAliasRequest(
            session_id=str(session_id), alias_name=alias_name, dataset_name=dataset_name
        )
        self.stub.DeleteAlias(request)
