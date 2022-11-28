import logging
import traceback
from uuid import UUID

import grpc
from dataclay.metadata.managers.object import ObjectMetadata
from dataclay_common.protos import (
    common_messages_pb2,
    metadata_service_pb2,
    metadata_service_pb2_grpc,
)
from google.protobuf.empty_pb2 import Empty

logger = logging.getLogger(__name__)


class MetadataServicer(metadata_service_pb2_grpc.MetadataServiceServicer):
    """Provides methods that implement functionality of metadata server"""

    def __init__(self, metadata_service):
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

    def GetDataclayID(self, _, context):
        try:
            dataclay_id = self.metadata_service.get_dataclay_id()
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return metadata_service_pb2.GetDataclayIDResponse()
        return metadata_service_pb2.GetDataclayIDResponse(dataclay_id=str(dataclay_id))

    def GetAllExecutionEnvironments(self, request, context):
        try:
            exec_envs = self.metadata_service.get_all_execution_environments(
                request.language, request.get_external, request.from_backend
            )
            response = dict()
            for id, exec_env in exec_envs.items():
                response[str(id)] = exec_env.get_proto()
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return metadata_service_pb2.GetAllExecutionEnvironmentsResponse()
        return metadata_service_pb2.GetAllExecutionEnvironmentsResponse(exec_envs=response)

    # TODO: Remove it. EE can access ETCD directly.
    def AutoregisterEE(self, request, context):
        try:
            self.metadata_service.autoregister_ee(
                UUID(request.id), request.hostname, request.port, request.sl_name, request.lang
            )
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()
        return Empty()

    ###################
    # Object Metadata #
    ###################

    # TODO: Remove it. Only EE should be able to call it.
    def RegisterObject(self, request, context):
        try:
            object_md = ObjectMetadata.from_proto(request.object_md)
            self.metadata_service.register_object(UUID(request.session_id), object_md)
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
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return common_messages_pb2.ObjectMetadata()
        return object_md.get_proto()

    def DeleteAlias(self, request, context):
        try:
            self.metadata_service.delete_alias(
                UUID(request.session_id),
                request.alias_name,
                request.dataset_name,
                check_session=True,
            )
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()
            return Empty()
        return Empty()
