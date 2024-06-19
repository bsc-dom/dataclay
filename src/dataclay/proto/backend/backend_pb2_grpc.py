# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings

from dataclay.proto.backend import backend_pb2 as dataclay_dot_proto_dot_backend_dot_backend__pb2
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from google.protobuf import wrappers_pb2 as google_dot_protobuf_dot_wrappers__pb2

GRPC_GENERATED_VERSION = '1.64.1'
GRPC_VERSION = grpc.__version__
EXPECTED_ERROR_RELEASE = '1.65.0'
SCHEDULED_RELEASE_DATE = 'June 25, 2024'
_version_not_supported = False

try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True

if _version_not_supported:
    warnings.warn(
        f'The grpc package installed is at version {GRPC_VERSION},'
        + f' but the generated code in dataclay/proto/backend/backend_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
        + f' This warning will become an error in {EXPECTED_ERROR_RELEASE},'
        + f' scheduled for release on {SCHEDULED_RELEASE_DATE}.',
        RuntimeWarning
    )


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
                _registered_method=True)
        self.CallActiveMethod = channel.unary_unary(
                '/dataclay.proto.backend.BackendService/CallActiveMethod',
                request_serializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.CallActiveMethodRequest.SerializeToString,
                response_deserializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.CallActiveMethodResponse.FromString,
                _registered_method=True)
        self.GetObjectAttribute = channel.unary_unary(
                '/dataclay.proto.backend.BackendService/GetObjectAttribute',
                request_serializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.GetObjectAttributeRequest.SerializeToString,
                response_deserializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.GetObjectAttributeResponse.FromString,
                _registered_method=True)
        self.SetObjectAttribute = channel.unary_unary(
                '/dataclay.proto.backend.BackendService/SetObjectAttribute',
                request_serializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.SetObjectAttributeRequest.SerializeToString,
                response_deserializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.SetObjectAttributeResponse.FromString,
                _registered_method=True)
        self.DelObjectAttribute = channel.unary_unary(
                '/dataclay.proto.backend.BackendService/DelObjectAttribute',
                request_serializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.DelObjectAttributeRequest.SerializeToString,
                response_deserializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.DelObjectAttributeResponse.FromString,
                _registered_method=True)
        self.GetObjectProperties = channel.unary_unary(
                '/dataclay.proto.backend.BackendService/GetObjectProperties',
                request_serializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.GetObjectPropertiesRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_wrappers__pb2.BytesValue.FromString,
                _registered_method=True)
        self.UpdateObjectProperties = channel.unary_unary(
                '/dataclay.proto.backend.BackendService/UpdateObjectProperties',
                request_serializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.UpdateObjectPropertiesRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                _registered_method=True)
        self.SendObjects = channel.unary_unary(
                '/dataclay.proto.backend.BackendService/SendObjects',
                request_serializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.SendObjectsRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                _registered_method=True)
        self.RegisterObjects = channel.unary_unary(
                '/dataclay.proto.backend.BackendService/RegisterObjects',
                request_serializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.RegisterObjectsRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                _registered_method=True)
        self.NewObjectVersion = channel.unary_unary(
                '/dataclay.proto.backend.BackendService/NewObjectVersion',
                request_serializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.NewObjectVersionRequest.SerializeToString,
                response_deserializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.NewObjectVersionResponse.FromString,
                _registered_method=True)
        self.ConsolidateObjectVersion = channel.unary_unary(
                '/dataclay.proto.backend.BackendService/ConsolidateObjectVersion',
                request_serializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.ConsolidateObjectVersionRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                _registered_method=True)
        self.ProxifyObject = channel.unary_unary(
                '/dataclay.proto.backend.BackendService/ProxifyObject',
                request_serializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.ProxifyObjectRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                _registered_method=True)
        self.ChangeObjectId = channel.unary_unary(
                '/dataclay.proto.backend.BackendService/ChangeObjectId',
                request_serializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.ChangeObjectIdRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                _registered_method=True)
        self.NewObjectReplica = channel.unary_unary(
                '/dataclay.proto.backend.BackendService/NewObjectReplica',
                request_serializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.NewObjectReplicaRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                _registered_method=True)
        self.FlushAll = channel.unary_unary(
                '/dataclay.proto.backend.BackendService/FlushAll',
                request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                _registered_method=True)
        self.Stop = channel.unary_unary(
                '/dataclay.proto.backend.BackendService/Stop',
                request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                _registered_method=True)
        self.Drain = channel.unary_unary(
                '/dataclay.proto.backend.BackendService/Drain',
                request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                _registered_method=True)


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

    def GetObjectAttribute(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SetObjectAttribute(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def DelObjectAttribute(self, request, context):
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

    def SendObjects(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RegisterObjects(self, request, context):
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

    def NewObjectReplica(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def FlushAll(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Stop(self, request, context):
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
            'GetObjectAttribute': grpc.unary_unary_rpc_method_handler(
                    servicer.GetObjectAttribute,
                    request_deserializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.GetObjectAttributeRequest.FromString,
                    response_serializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.GetObjectAttributeResponse.SerializeToString,
            ),
            'SetObjectAttribute': grpc.unary_unary_rpc_method_handler(
                    servicer.SetObjectAttribute,
                    request_deserializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.SetObjectAttributeRequest.FromString,
                    response_serializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.SetObjectAttributeResponse.SerializeToString,
            ),
            'DelObjectAttribute': grpc.unary_unary_rpc_method_handler(
                    servicer.DelObjectAttribute,
                    request_deserializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.DelObjectAttributeRequest.FromString,
                    response_serializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.DelObjectAttributeResponse.SerializeToString,
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
            'SendObjects': grpc.unary_unary_rpc_method_handler(
                    servicer.SendObjects,
                    request_deserializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.SendObjectsRequest.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
            'RegisterObjects': grpc.unary_unary_rpc_method_handler(
                    servicer.RegisterObjects,
                    request_deserializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.RegisterObjectsRequest.FromString,
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
            'NewObjectReplica': grpc.unary_unary_rpc_method_handler(
                    servicer.NewObjectReplica,
                    request_deserializer=dataclay_dot_proto_dot_backend_dot_backend__pb2.NewObjectReplicaRequest.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
            'FlushAll': grpc.unary_unary_rpc_method_handler(
                    servicer.FlushAll,
                    request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
            'Stop': grpc.unary_unary_rpc_method_handler(
                    servicer.Stop,
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
    server.add_registered_method_handlers('dataclay.proto.backend.BackendService', rpc_method_handlers)


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
        return grpc.experimental.unary_unary(
            request,
            target,
            '/dataclay.proto.backend.BackendService/MakePersistent',
            dataclay_dot_proto_dot_backend_dot_backend__pb2.MakePersistentRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

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
        return grpc.experimental.unary_unary(
            request,
            target,
            '/dataclay.proto.backend.BackendService/CallActiveMethod',
            dataclay_dot_proto_dot_backend_dot_backend__pb2.CallActiveMethodRequest.SerializeToString,
            dataclay_dot_proto_dot_backend_dot_backend__pb2.CallActiveMethodResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def GetObjectAttribute(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/dataclay.proto.backend.BackendService/GetObjectAttribute',
            dataclay_dot_proto_dot_backend_dot_backend__pb2.GetObjectAttributeRequest.SerializeToString,
            dataclay_dot_proto_dot_backend_dot_backend__pb2.GetObjectAttributeResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def SetObjectAttribute(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/dataclay.proto.backend.BackendService/SetObjectAttribute',
            dataclay_dot_proto_dot_backend_dot_backend__pb2.SetObjectAttributeRequest.SerializeToString,
            dataclay_dot_proto_dot_backend_dot_backend__pb2.SetObjectAttributeResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def DelObjectAttribute(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/dataclay.proto.backend.BackendService/DelObjectAttribute',
            dataclay_dot_proto_dot_backend_dot_backend__pb2.DelObjectAttributeRequest.SerializeToString,
            dataclay_dot_proto_dot_backend_dot_backend__pb2.DelObjectAttributeResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

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
        return grpc.experimental.unary_unary(
            request,
            target,
            '/dataclay.proto.backend.BackendService/GetObjectProperties',
            dataclay_dot_proto_dot_backend_dot_backend__pb2.GetObjectPropertiesRequest.SerializeToString,
            google_dot_protobuf_dot_wrappers__pb2.BytesValue.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

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
        return grpc.experimental.unary_unary(
            request,
            target,
            '/dataclay.proto.backend.BackendService/UpdateObjectProperties',
            dataclay_dot_proto_dot_backend_dot_backend__pb2.UpdateObjectPropertiesRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

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
        return grpc.experimental.unary_unary(
            request,
            target,
            '/dataclay.proto.backend.BackendService/SendObjects',
            dataclay_dot_proto_dot_backend_dot_backend__pb2.SendObjectsRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def RegisterObjects(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/dataclay.proto.backend.BackendService/RegisterObjects',
            dataclay_dot_proto_dot_backend_dot_backend__pb2.RegisterObjectsRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

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
        return grpc.experimental.unary_unary(
            request,
            target,
            '/dataclay.proto.backend.BackendService/NewObjectVersion',
            dataclay_dot_proto_dot_backend_dot_backend__pb2.NewObjectVersionRequest.SerializeToString,
            dataclay_dot_proto_dot_backend_dot_backend__pb2.NewObjectVersionResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

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
        return grpc.experimental.unary_unary(
            request,
            target,
            '/dataclay.proto.backend.BackendService/ConsolidateObjectVersion',
            dataclay_dot_proto_dot_backend_dot_backend__pb2.ConsolidateObjectVersionRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

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
        return grpc.experimental.unary_unary(
            request,
            target,
            '/dataclay.proto.backend.BackendService/ProxifyObject',
            dataclay_dot_proto_dot_backend_dot_backend__pb2.ProxifyObjectRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

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
        return grpc.experimental.unary_unary(
            request,
            target,
            '/dataclay.proto.backend.BackendService/ChangeObjectId',
            dataclay_dot_proto_dot_backend_dot_backend__pb2.ChangeObjectIdRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def NewObjectReplica(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/dataclay.proto.backend.BackendService/NewObjectReplica',
            dataclay_dot_proto_dot_backend_dot_backend__pb2.NewObjectReplicaRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

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
        return grpc.experimental.unary_unary(
            request,
            target,
            '/dataclay.proto.backend.BackendService/FlushAll',
            google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def Stop(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/dataclay.proto.backend.BackendService/Stop',
            google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

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
        return grpc.experimental.unary_unary(
            request,
            target,
            '/dataclay.proto.backend.BackendService/Drain',
            google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)
