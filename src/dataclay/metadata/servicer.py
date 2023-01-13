from __future__ import annotations

import logging
import traceback
from uuid import UUID

import grpc
from google.protobuf.empty_pb2 import Empty

from dataclay.metadata.managers.kvdata import ObjectMetadata
from dataclay.protos import (
    common_messages_pb2,
    metadata_service_pb2,
    metadata_service_pb2_grpc,
)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dataclay.metadata.api import MetadataAPI


logger = logging.getLogger(__name__)


class MetadataServicer(metadata_service_pb2_grpc.MetadataServiceServicer):
    """Provides methods that implement functionality of metadata server"""

    def __init__(self, metadata_service: MetadataAPI):
        self.metadata_service = metadata_service
        logger.debug("Initialized MetadataServiceServicer")

    # TODO: define get_exception_info(..) to serialize excpetions

    def NewAccount(self, request, context):
        try:
            self.metadata_service.new_account(request.username, request.password)
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()
        return Empty()

    def NewSession(self, request, context):
        try:
            session = self.metadata_service.new_session(
                request.username, request.password, request.dataset_name
            )
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return common_messages_pb2.Session()
        return session.get_proto()

    def NewDataset(self, request, context):
        try:
            self.metadata_service.new_dataset(request.username, request.password, request.dataset)
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()
        return Empty()

    def CloseSession(self, request, context):
        try:
            self.metadata_service.close_session(UUID(request.id))
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()
        return Empty()

    def GetDataclay(self, request, context):
        try:
            dataclay = self.metadata_service.get_dataclay(UUID(request.dataclay_id))
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return common_messages_pb2.Dataclay()
        return dataclay.get_proto()

    def GetAllBackends(self, request, context):
        try:
            backends = self.metadata_service.get_all_backends(request.from_backend)
            response = dict()
            for id, backend in backends.items():
                response[str(id)] = backend.get_proto()
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return metadata_service_pb2.GetAllBackendsResponse()
        return metadata_service_pb2.GetAllBackendsResponse(backends=response)

    ###################
    # Object Metadata #
    ###################

    # TODO: Remove it. Only EE should be able to call it.
    def RegisterObject(self, request, context):
        try:
            object_md = ObjectMetadata.from_proto(request.object_md)
            self.metadata_service.register_object(object_md, UUID(request.session_id))
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()
        return Empty()

    def GetObjectMDById(self, request, context):
        try:
            object_md = self.metadata_service.get_object_md_by_id(
                UUID(request.object_id),
                UUID(request.session_id),
                check_session=True,
            )
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return common_messages_pb2.ObjectMetadata()
        return object_md.get_proto()

    def GetObjectMDByAlias(self, request, context):
        try:
            object_md = self.metadata_service.get_object_md_by_alias(
                request.alias_name,
                request.dataset_name,
                UUID(request.session_id),
                check_session=True,
            )
        except Exception as e:
            traceback.print_exc()
            context.abort(grpc.StatusCode.INTERNAL, str(e))
        return object_md.get_proto()

    def DeleteAlias(self, request, context):
        try:
            self.metadata_service.delete_alias(
                request.alias_name,
                request.dataset_name,
                UUID(request.session_id),
                check_session=True,
            )
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()
        return Empty()
