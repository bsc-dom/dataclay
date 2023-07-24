# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from dataclay.proto.backend import backend_pb2 as dataclay_dot_proto_dot_backend_dot_backend__pb2
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from google.protobuf import wrappers_pb2 as google_dot_protobuf_dot_wrappers__pb2


class BackendServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.MakePersistent = channel.unary_unary(
                '/dataclay.proto.backend.BackendService/MakePersistent',
                request_serializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.MakePersistentRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                )
        self.CallActiveMethod = channel.unary_unary(
                '/dataclay.proto.backend.BackendService/CallActiveMethod',
                request_serializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.CallActiveMethodRequest.SerializeToString,
                response_deserializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.CallActiveMethodResponse.FromString,
                )
        self.GetObjectProperties = channel.unary_unary(
                '/dataclay.proto.backend.BackendService/GetObjectProperties',
                request_serializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.GetObjectPropertiesRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_wrappers__pb2.BytesValue.FromString,
                )
        self.UpdateObjectProperties = channel.unary_unary(
                '/dataclay.proto.backend.BackendService/UpdateObjectProperties',
                request_serializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.UpdateObjectPropertiesRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                )
        self.MoveObjects = channel.unary_unary(
                '/dataclay.proto.backend.BackendService/MoveObjects',
                request_serializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.MoveObjectsRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                )
        self.SendObjects = channel.unary_unary(
                '/dataclay.proto.backend.BackendService/SendObjects',
                request_serializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.SendObjectsRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                )
        self.NewObjectVersion = channel.unary_unary(
                '/dataclay.proto.backend.BackendService/NewObjectVersion',
                request_serializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.NewObjectVersionRequest.SerializeToString,
                response_deserializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.NewObjectVersionResponse.FromString,
                )
        self.ConsolidateObjectVersion = channel.unary_unary(
                '/dataclay.proto.backend.BackendService/ConsolidateObjectVersion',
                request_serializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.ConsolidateObjectVersionRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                )
        self.ProxifyObject = channel.unary_unary(
                '/dataclay.proto.backend.BackendService/ProxifyObject',
                request_serializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.ProxifyObjectRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                )
        self.ChangeObjectId = channel.unary_unary(
                '/dataclay.proto.backend.BackendService/ChangeObjectId',
                request_serializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.ChangeObjectIdRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                )
        self.FlushAll = channel.unary_unary(
                '/dataclay.proto.backend.BackendService/FlushAll',
                request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                )
        self.Shutdown = channel.unary_unary(
                '/dataclay.proto.backend.BackendService/Shutdown',
                request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                )
        self.Drain = channel.unary_unary(
                '/dataclay.proto.backend.BackendService/Drain',
                request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                )


class BackendServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def MakePersistent(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def CallActiveMethod(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetObjectProperties(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def UpdateObjectProperties(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def MoveObjects(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SendObjects(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def NewObjectVersion(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ConsolidateObjectVersion(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ProxifyObject(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ChangeObjectId(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def FlushAll(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Shutdown(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Drain(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_BackendServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'MakePersistent': grpc.unary_unary_rpc_method_handler(
                    servicer.MakePersistent,
                    request_deserializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.MakePersistentRequest.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
            'CallActiveMethod': grpc.unary_unary_rpc_method_handler(
                    servicer.CallActiveMethod,
                    request_deserializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.CallActiveMethodRequest.FromString,
                    response_serializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.CallActiveMethodResponse.SerializeToString,
            ),
            'GetObjectProperties': grpc.unary_unary_rpc_method_handler(
                    servicer.GetObjectProperties,
                    request_deserializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.GetObjectPropertiesRequest.FromString,
                    response_serializer=google_dot_protobuf_dot_wrappers__pb2.BytesValue.SerializeToString,
            ),
            'UpdateObjectProperties': grpc.unary_unary_rpc_method_handler(
                    servicer.UpdateObjectProperties,
                    request_deserializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.UpdateObjectPropertiesRequest.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
            'MoveObjects': grpc.unary_unary_rpc_method_handler(
                    servicer.MoveObjects,
                    request_deserializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.MoveObjectsRequest.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
            'SendObjects': grpc.unary_unary_rpc_method_handler(
                    servicer.SendObjects,
                    request_deserializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.SendObjectsRequest.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
            'NewObjectVersion': grpc.unary_unary_rpc_method_handler(
                    servicer.NewObjectVersion,
                    request_deserializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.NewObjectVersionRequest.FromString,
                    response_serializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.NewObjectVersionResponse.SerializeToString,
            ),
            'ConsolidateObjectVersion': grpc.unary_unary_rpc_method_handler(
                    servicer.ConsolidateObjectVersion,
                    request_deserializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.ConsolidateObjectVersionRequest.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
            'ProxifyObject': grpc.unary_unary_rpc_method_handler(
                    servicer.ProxifyObject,
                    request_deserializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.ProxifyObjectRequest.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
            'ChangeObjectId': grpc.unary_unary_rpc_method_handler(
                    servicer.ChangeObjectId,
                    request_deserializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.ChangeObjectIdRequest.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
            'FlushAll': grpc.unary_unary_rpc_method_handler(
                    servicer.FlushAll,
                    request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
            'Shutdown': grpc.unary_unary_rpc_method_handler(
                    servicer.Shutdown,
                    request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
            'Drain': grpc.unary_unary_rpc_method_handler(
                    servicer.Drain,
                    request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'dataclay.proto.backend.BackendService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class BackendService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def MakePersistent(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dataclay.proto.backend.BackendService/MakePersistent',
            dataclay_dot_proto_dot_backend_dot_backend__pb2.MakePersistentRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def CallActiveMethod(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dataclay.proto.backend.BackendService/CallActiveMethod',
            dataclay_dot_proto_dot_backend_dot_backend__pb2.CallActiveMethodRequest.SerializeToString,
            dataclay_dot_proto_dot_backend_dot_backend__pb2.CallActiveMethodResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetObjectProperties(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dataclay.proto.backend.BackendService/GetObjectProperties',
            dataclay_dot_proto_dot_backend_dot_backend__pb2.GetObjectPropertiesRequest.SerializeToString,
            google_dot_protobuf_dot_wrappers__pb2.BytesValue.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def UpdateObjectProperties(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dataclay.proto.backend.BackendService/UpdateObjectProperties',
            dataclay_dot_proto_dot_backend_dot_backend__pb2.UpdateObjectPropertiesRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def MoveObjects(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dataclay.proto.backend.BackendService/MoveObjects',
            dataclay_dot_proto_dot_backend_dot_backend__pb2.MoveObjectsRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SendObjects(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dataclay.proto.backend.BackendService/SendObjects',
            dataclay_dot_proto_dot_backend_dot_backend__pb2.SendObjectsRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def NewObjectVersion(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dataclay.proto.backend.BackendService/NewObjectVersion',
            dataclay_dot_proto_dot_backend_dot_backend__pb2.NewObjectVersionRequest.SerializeToString,
            dataclay_dot_proto_dot_backend_dot_backend__pb2.NewObjectVersionResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def ConsolidateObjectVersion(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dataclay.proto.backend.BackendService/ConsolidateObjectVersion',
            dataclay_dot_proto_dot_backend_dot_backend__pb2.ConsolidateObjectVersionRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def ProxifyObject(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dataclay.proto.backend.BackendService/ProxifyObject',
            dataclay_dot_proto_dot_backend_dot_backend__pb2.ProxifyObjectRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def ChangeObjectId(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dataclay.proto.backend.BackendService/ChangeObjectId',
            dataclay_dot_proto_dot_backend_dot_backend__pb2.ChangeObjectIdRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def FlushAll(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dataclay.proto.backend.BackendService/FlushAll',
            google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Shutdown(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dataclay.proto.backend.BackendService/Shutdown',
            google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Drain(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dataclay.proto.backend.BackendService/Drain',
            google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
