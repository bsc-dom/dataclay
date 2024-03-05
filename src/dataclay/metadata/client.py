import atexit
import logging
from typing import Optional
from uuid import UUID

import grpc
from google.protobuf.empty_pb2 import Empty

from dataclay.metadata.kvdata import Alias, Backend, Dataclay, ObjectMetadata
from dataclay.proto.metadata import metadata_pb2, metadata_pb2_grpc
from dataclay.utils.decorators import grpc_error_handler
from dataclay.utils.uuid import str_to_uuid, uuid_to_str

logger = logging.getLogger(__name__)


class MetadataClient:
    def __init__(self, host: str, port: int):
        self.address = f"{host}:{port}"
        self.channel = grpc.insecure_channel(self.address)
        self.stub = metadata_pb2_grpc.MetadataServiceStub(self.channel)
        # atexit.register(self.close)

    def is_ready(self, timeout: Optional[float] = None):
        try:
            grpc.channel_ready_future(self.channel).result(timeout)
            return True
        except grpc.FutureTimeoutError:
            return False

    def close(self):
        self.channel.close()

    ###################
    # Account Manager #
    ###################

    @grpc_error_handler
    def new_account(self, username: str, password: str):
        request = metadata_pb2.NewAccountRequest(username=username, password=password)
        self.stub.NewAccount(request)

    ###################
    # Dataset Manager #
    ###################

    @grpc_error_handler
    def new_dataset(self, username: str, password: str, dataset: str):
        request = metadata_pb2.NewDatasetRequest(
            username=username, password=password, dataset=dataset
        )
        self.stub.NewDataset(request)

    #####################
    # Dataclay Metadata #
    #####################

    @grpc_error_handler
    def get_dataclay(self, id: UUID) -> Dataclay:
        request = metadata_pb2.GetDataclayRequest(dataclay_id=str(id))
        response = self.stub.GetDataclay(request)
        return Dataclay.from_proto(response)

    #####################
    # EE-SL information #
    #####################

    @grpc_error_handler
    def get_all_backends(
        self, from_backend: bool = False, force: bool = True
    ) -> dict[UUID, Backend]:
        request = metadata_pb2.GetAllBackendsRequest(from_backend=from_backend, force=force)
        response = self.stub.GetAllBackends(request)

        result = {}
        for id, proto in response.backends.items():
            result[UUID(id)] = Backend.from_proto(proto)
        return result

    ###################
    # Object Metadata #
    ###################

    @grpc_error_handler
    def get_all_objects(self) -> dict[UUID, ObjectMetadata]:
        response = self.stub.GetAllObjects(Empty())

        result = {}
        for id, proto in response.objects.items():
            result[UUID(id)] = ObjectMetadata.from_proto(proto)
        return result

    @grpc_error_handler
    def get_object_md_by_id(self, object_id: UUID) -> ObjectMetadata:
        request = metadata_pb2.GetObjectMDByIdRequest(object_id=str(object_id))
        object_md_proto = self.stub.GetObjectMDById(request)
        return ObjectMetadata.from_proto(object_md_proto)

    @grpc_error_handler
    def get_object_md_by_alias(self, alias_name: str, dataset_name: str) -> ObjectMetadata:
        request = metadata_pb2.GetObjectMDByAliasRequest(
            alias_name=alias_name, dataset_name=dataset_name
        )
        object_md_proto = self.stub.GetObjectMDByAlias(request)
        return ObjectMetadata.from_proto(object_md_proto)

    #########
    # Alias #
    #########

    @grpc_error_handler
    def new_alias(self, alias_name: str, dataset_name: str, object_id: UUID):
        request = metadata_pb2.NewAliasRequest(
            alias_name=alias_name,
            dataset_name=dataset_name,
            object_id=str(object_id),
        )
        self.stub.NewAlias(request)

    @grpc_error_handler
    def get_all_alias(self, dataset_name: str, object_id: UUID) -> dict[str, Alias]:
        request = metadata_pb2.GetAllAliasRequest(
            dataset_name=dataset_name, object_id=uuid_to_str(object_id)
        )
        response = self.stub.GetAllAlias(request)

        result = {}
        for alias_name, proto in response.aliases.items():
            result[alias_name] = Alias.from_proto(proto)
        return result

    @grpc_error_handler
    def delete_alias(self, alias_name: str, dataset_name: str):
        request = metadata_pb2.DeleteAliasRequest(alias_name=alias_name, dataset_name=dataset_name)
        self.stub.DeleteAlias(request)

    @grpc_error_handler
    def stop(self):
        self.stub.Stop(Empty())
