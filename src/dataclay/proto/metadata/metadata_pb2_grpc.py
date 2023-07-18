# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from dataclay.proto.common import common_pb2 as dataclay_dot_proto_dot_common_dot_common__pb2
from dataclay.proto.metadata import metadata_pb2 as dataclay_dot_proto_dot_metadata_dot_metadata__pb2
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2


class MetadataServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.NewAccount = channel.unary_unary(
                '/dataclay.proto.metadata.MetadataService/NewAccount',
                request_serializer=dataclay_dot_proto_dot_metadata_dot_metadata__pb2.NewAccountRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                )
        self.GetAccount = channel.unary_unary(
                '/dataclay.proto.metadata.MetadataService/GetAccount',
                request_serializer=dataclay_dot_proto_dot_metadata_dot_metadata__pb2.GetAccountRequest.SerializeToString,
                response_deserializer=dataclay_dot_proto_dot_metadata_dot_metadata__pb2.GetAccountResponse.FromString,
                )
        self.NewSession = channel.unary_unary(
                '/dataclay.proto.metadata.MetadataService/NewSession',
                request_serializer=dataclay_dot_proto_dot_metadata_dot_metadata__pb2.NewSessionRequest.SerializeToString,
                response_deserializer=dataclay_dot_proto_dot_common_dot_common__pb2.Session.FromString,
                )
        self.CloseSession = channel.unary_unary(
                '/dataclay.proto.metadata.MetadataService/CloseSession',
                request_serializer=dataclay_dot_proto_dot_metadata_dot_metadata__pb2.CloseSessionRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                )
        self.NewDataset = channel.unary_unary(
                '/dataclay.proto.metadata.MetadataService/NewDataset',
                request_serializer=dataclay_dot_proto_dot_metadata_dot_metadata__pb2.NewDatasetRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                )
        self.GetAllBackends = channel.unary_unary(
                '/dataclay.proto.metadata.MetadataService/GetAllBackends',
                request_serializer=dataclay_dot_proto_dot_metadata_dot_metadata__pb2.GetAllBackendsRequest.SerializeToString,
                response_deserializer=dataclay_dot_proto_dot_metadata_dot_metadata__pb2.GetAllBackendsResponse.FromString,
                )
        self.GetDataclay = channel.unary_unary(
                '/dataclay.proto.metadata.MetadataService/GetDataclay',
                request_serializer=dataclay_dot_proto_dot_metadata_dot_metadata__pb2.GetDataclayRequest.SerializeToString,
                response_deserializer=dataclay_dot_proto_dot_common_dot_common__pb2.Dataclay.FromString,
                )
        self.RegisterObject = channel.unary_unary(
                '/dataclay.proto.metadata.MetadataService/RegisterObject',
                request_serializer=dataclay_dot_proto_dot_metadata_dot_metadata__pb2.RegisterObjectRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                )
        self.GetObjectMDById = channel.unary_unary(
                '/dataclay.proto.metadata.MetadataService/GetObjectMDById',
                request_serializer=dataclay_dot_proto_dot_metadata_dot_metadata__pb2.GetObjectMDByIdRequest.SerializeToString,
                response_deserializer=dataclay_dot_proto_dot_common_dot_common__pb2.ObjectMetadata.FromString,
                )
        self.GetObjectMDByAlias = channel.unary_unary(
                '/dataclay.proto.metadata.MetadataService/GetObjectMDByAlias',
                request_serializer=dataclay_dot_proto_dot_metadata_dot_metadata__pb2.GetObjectMDByAliasRequest.SerializeToString,
                response_deserializer=dataclay_dot_proto_dot_common_dot_common__pb2.ObjectMetadata.FromString,
                )
        self.GetAllObjects = channel.unary_unary(
                '/dataclay.proto.metadata.MetadataService/GetAllObjects',
                request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
                response_deserializer=dataclay_dot_proto_dot_metadata_dot_metadata__pb2.GetAllObjectsResponse.FromString,
                )
        self.DeleteAlias = channel.unary_unary(
                '/dataclay.proto.metadata.MetadataService/DeleteAlias',
                request_serializer=dataclay_dot_proto_dot_metadata_dot_metadata__pb2.DeleteAliasRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                )
        self.NewAlias = channel.unary_unary(
                '/dataclay.proto.metadata.MetadataService/NewAlias',
                request_serializer=dataclay_dot_proto_dot_metadata_dot_metadata__pb2.NewAliasRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                )
        self.GetAllAlias = channel.unary_unary(
                '/dataclay.proto.metadata.MetadataService/GetAllAlias',
                request_serializer=dataclay_dot_proto_dot_metadata_dot_metadata__pb2.GetAllAliasRequest.SerializeToString,
                response_deserializer=dataclay_dot_proto_dot_metadata_dot_metadata__pb2.GetAllAliasResponse.FromString,
                )


class MetadataServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def NewAccount(self, request, context):
        """Account Manager
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetAccount(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def NewSession(self, request, context):
        """Session Manager
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def CloseSession(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def NewDataset(self, request, context):
        """Dataset Manager
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetAllBackends(self, request, context):
        """EE-SL information
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetDataclay(self, request, context):
        """Federation
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RegisterObject(self, request, context):
        """Object Metadata
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetObjectMDById(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetObjectMDByAlias(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetAllObjects(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def DeleteAlias(self, request, context):
        """Alias
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def NewAlias(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetAllAlias(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_MetadataServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'NewAccount': grpc.unary_unary_rpc_method_handler(
                    servicer.NewAccount,
                    request_deserializer=dataclay_dot_proto_dot_metadata_dot_metadata__pb2.NewAccountRequest.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
            'GetAccount': grpc.unary_unary_rpc_method_handler(
                    servicer.GetAccount,
                    request_deserializer=dataclay_dot_proto_dot_metadata_dot_metadata__pb2.GetAccountRequest.FromString,
                    response_serializer=dataclay_dot_proto_dot_metadata_dot_metadata__pb2.GetAccountResponse.SerializeToString,
            ),
            'NewSession': grpc.unary_unary_rpc_method_handler(
                    servicer.NewSession,
                    request_deserializer=dataclay_dot_proto_dot_metadata_dot_metadata__pb2.NewSessionRequest.FromString,
                    response_serializer=dataclay_dot_proto_dot_common_dot_common__pb2.Session.SerializeToString,
            ),
            'CloseSession': grpc.unary_unary_rpc_method_handler(
                    servicer.CloseSession,
                    request_deserializer=dataclay_dot_proto_dot_metadata_dot_metadata__pb2.CloseSessionRequest.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
            'NewDataset': grpc.unary_unary_rpc_method_handler(
                    servicer.NewDataset,
                    request_deserializer=dataclay_dot_proto_dot_metadata_dot_metadata__pb2.NewDatasetRequest.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
            'GetAllBackends': grpc.unary_unary_rpc_method_handler(
                    servicer.GetAllBackends,
                    request_deserializer=dataclay_dot_proto_dot_metadata_dot_metadata__pb2.GetAllBackendsRequest.FromString,
                    response_serializer=dataclay_dot_proto_dot_metadata_dot_metadata__pb2.GetAllBackendsResponse.SerializeToString,
            ),
            'GetDataclay': grpc.unary_unary_rpc_method_handler(
                    servicer.GetDataclay,
                    request_deserializer=dataclay_dot_proto_dot_metadata_dot_metadata__pb2.GetDataclayRequest.FromString,
                    response_serializer=dataclay_dot_proto_dot_common_dot_common__pb2.Dataclay.SerializeToString,
            ),
            'RegisterObject': grpc.unary_unary_rpc_method_handler(
                    servicer.RegisterObject,
                    request_deserializer=dataclay_dot_proto_dot_metadata_dot_metadata__pb2.RegisterObjectRequest.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
            'GetObjectMDById': grpc.unary_unary_rpc_method_handler(
                    servicer.GetObjectMDById,
                    request_deserializer=dataclay_dot_proto_dot_metadata_dot_metadata__pb2.GetObjectMDByIdRequest.FromString,
                    response_serializer=dataclay_dot_proto_dot_common_dot_common__pb2.ObjectMetadata.SerializeToString,
            ),
            'GetObjectMDByAlias': grpc.unary_unary_rpc_method_handler(
                    servicer.GetObjectMDByAlias,
                    request_deserializer=dataclay_dot_proto_dot_metadata_dot_metadata__pb2.GetObjectMDByAliasRequest.FromString,
                    response_serializer=dataclay_dot_proto_dot_common_dot_common__pb2.ObjectMetadata.SerializeToString,
            ),
            'GetAllObjects': grpc.unary_unary_rpc_method_handler(
                    servicer.GetAllObjects,
                    request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                    response_serializer=dataclay_dot_proto_dot_metadata_dot_metadata__pb2.GetAllObjectsResponse.SerializeToString,
            ),
            'DeleteAlias': grpc.unary_unary_rpc_method_handler(
                    servicer.DeleteAlias,
                    request_deserializer=dataclay_dot_proto_dot_metadata_dot_metadata__pb2.DeleteAliasRequest.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
            'NewAlias': grpc.unary_unary_rpc_method_handler(
                    servicer.NewAlias,
                    request_deserializer=dataclay_dot_proto_dot_metadata_dot_metadata__pb2.NewAliasRequest.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
            'GetAllAlias': grpc.unary_unary_rpc_method_handler(
                    servicer.GetAllAlias,
                    request_deserializer=dataclay_dot_proto_dot_metadata_dot_metadata__pb2.GetAllAliasRequest.FromString,
                    response_serializer=dataclay_dot_proto_dot_metadata_dot_metadata__pb2.GetAllAliasResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'dataclay.proto.metadata.MetadataService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class MetadataService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def NewAccount(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dataclay.proto.metadata.MetadataService/NewAccount',
            dataclay_dot_proto_dot_metadata_dot_metadata__pb2.NewAccountRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetAccount(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dataclay.proto.metadata.MetadataService/GetAccount',
            dataclay_dot_proto_dot_metadata_dot_metadata__pb2.GetAccountRequest.SerializeToString,
            dataclay_dot_proto_dot_metadata_dot_metadata__pb2.GetAccountResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def NewSession(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dataclay.proto.metadata.MetadataService/NewSession',
            dataclay_dot_proto_dot_metadata_dot_metadata__pb2.NewSessionRequest.SerializeToString,
            dataclay_dot_proto_dot_common_dot_common__pb2.Session.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def CloseSession(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dataclay.proto.metadata.MetadataService/CloseSession',
            dataclay_dot_proto_dot_metadata_dot_metadata__pb2.CloseSessionRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def NewDataset(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dataclay.proto.metadata.MetadataService/NewDataset',
            dataclay_dot_proto_dot_metadata_dot_metadata__pb2.NewDatasetRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetAllBackends(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dataclay.proto.metadata.MetadataService/GetAllBackends',
            dataclay_dot_proto_dot_metadata_dot_metadata__pb2.GetAllBackendsRequest.SerializeToString,
            dataclay_dot_proto_dot_metadata_dot_metadata__pb2.GetAllBackendsResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetDataclay(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dataclay.proto.metadata.MetadataService/GetDataclay',
            dataclay_dot_proto_dot_metadata_dot_metadata__pb2.GetDataclayRequest.SerializeToString,
            dataclay_dot_proto_dot_common_dot_common__pb2.Dataclay.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def RegisterObject(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dataclay.proto.metadata.MetadataService/RegisterObject',
            dataclay_dot_proto_dot_metadata_dot_metadata__pb2.RegisterObjectRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetObjectMDById(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dataclay.proto.metadata.MetadataService/GetObjectMDById',
            dataclay_dot_proto_dot_metadata_dot_metadata__pb2.GetObjectMDByIdRequest.SerializeToString,
            dataclay_dot_proto_dot_common_dot_common__pb2.ObjectMetadata.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetObjectMDByAlias(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dataclay.proto.metadata.MetadataService/GetObjectMDByAlias',
            dataclay_dot_proto_dot_metadata_dot_metadata__pb2.GetObjectMDByAliasRequest.SerializeToString,
            dataclay_dot_proto_dot_common_dot_common__pb2.ObjectMetadata.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetAllObjects(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dataclay.proto.metadata.MetadataService/GetAllObjects',
            google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            dataclay_dot_proto_dot_metadata_dot_metadata__pb2.GetAllObjectsResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def DeleteAlias(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dataclay.proto.metadata.MetadataService/DeleteAlias',
            dataclay_dot_proto_dot_metadata_dot_metadata__pb2.DeleteAliasRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def NewAlias(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dataclay.proto.metadata.MetadataService/NewAlias',
            dataclay_dot_proto_dot_metadata_dot_metadata__pb2.NewAliasRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetAllAlias(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dataclay.proto.metadata.MetadataService/GetAllAlias',
            dataclay_dot_proto_dot_metadata_dot_metadata__pb2.GetAllAliasRequest.SerializeToString,
            dataclay_dot_proto_dot_metadata_dot_metadata__pb2.GetAllAliasResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
