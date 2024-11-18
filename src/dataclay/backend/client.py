import logging
from typing import Any, Iterable, Optional
from uuid import UUID

import grpc
from google.protobuf import any_pb2, empty_pb2
from google.protobuf.wrappers_pb2 import BoolValue, FloatValue, Int32Value, StringValue
from grpc._cython.cygrpc import ChannelArgKey

import dataclay
from dataclay.config import session_var, settings
from dataclay.proto.backend import backend_pb2, backend_pb2_grpc
from dataclay.utils.decorators import grpc_aio_error_handler

logger = logging.getLogger(__name__)


class BackendClient:
    def __init__(self, host: str, port: int, backend_id: Optional[UUID] = None):
        """Create the stub and the channel at the address passed by the server.

        Optionally, the BackendID will be included in the metadata. It is not
        strictly needed, but it can be beneficial for sanity checking and also
        it is used for reverse proxy configurations.
        """
        self.id = backend_id
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
            self.channel = grpc.aio.insecure_channel(self.address, options)
            logger.info("SSL not configured")

        # Commented beause seems to fail with async
        # grpc.channel_ready_future(self.channel).result(timeout=settings.grpc_check_alive_timeout)
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

        self.channel = grpc.aio.secure_channel(self.address, credentials, options)

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
    async def is_ready(self, timeout: Optional[float] = None):
        try:
            await self.channel.channel_ready()  # TODO: Maybe put a timeout here
            return True
        except grpc.FutureTimeoutError:
            return False

    def close(self):
        """Closing channel by deleting channel and stub"""
        del self.channel
        del self.stub
        self.channel = None
        self.stub = None

    @grpc_aio_error_handler
    async def register_objects(self, dict_bytes: Iterable[bytes], make_replica: bool):
        request = backend_pb2.RegisterObjectsRequest(
            dict_bytes=dict_bytes, make_replica=make_replica
        )
        await self.stub.RegisterObjects(request, metadata=self.metadata_call)

    @grpc_aio_error_handler
    async def make_persistent(self, pickled_obj: Iterable[bytes]):
        request = backend_pb2.MakePersistentRequest(pickled_obj=pickled_obj)
        await self.stub.MakePersistent(request, metadata=self.metadata_call)

    @grpc_aio_error_handler
    async def call_active_method(
        self,
        object_id: UUID,
        method_name: str,
        args: bytes,
        kwargs: bytes,
        exec_constraints: dict[str, Any],
    ) -> tuple[bytes, bool]:

        converted_exec_constraints = {}
        for key, value in exec_constraints.items():
            any_value = any_pb2.Any()

            if isinstance(value, int) or value is None:
                wrapped_value = Int32Value(value=value)
            elif isinstance(value, float):
                wrapped_value = FloatValue(value=value)
            elif isinstance(value, str):
                wrapped_value = StringValue(value=value)
            elif isinstance(value, bool):
                wrapped_value = BoolValue(value=value)
            else:
                raise TypeError(f"Unsupported type {type(value)} for exec_constraints key '{key}'")

            any_value.Pack(wrapped_value)
            converted_exec_constraints[key] = any_value

        request = backend_pb2.CallActiveMethodRequest(
            object_id=str(object_id),
            method_name=method_name,
            args=args,
            kwargs=kwargs,
            exec_constraints=converted_exec_constraints,
        )

        current_context = session_var.get()

        metadata = self.metadata_call + [
            ("dataset-name", current_context["dataset_name"]),
            ("username", current_context["username"]),
            ("authorization", current_context["token"]),
        ]

        response = await self.stub.CallActiveMethod(request, metadata=metadata)
        return response.value, response.is_exception

    #################
    # Store Methods #
    #################

    @grpc_aio_error_handler
    async def get_object_attribute(self, object_id: UUID, attribute: str) -> tuple[bytes, bool]:
        request = backend_pb2.GetObjectAttributeRequest(
            object_id=str(object_id),
            attribute=attribute,
        )
        current_context = session_var.get()
        metadata = self.metadata_call + [
            ("username", current_context["username"]),
            ("authorization", current_context["token"]),
        ]
        response = await self.stub.GetObjectAttribute(request, metadata=metadata)
        return response.value, response.is_exception

    @grpc_aio_error_handler
    async def set_object_attribute(
        self, object_id: UUID, attribute: str, serialized_attribute: bytes
    ) -> tuple[bytes, bool]:
        request = backend_pb2.SetObjectAttributeRequest(
            object_id=str(object_id),
            attribute=attribute,
            serialized_attribute=serialized_attribute,
        )
        current_context = session_var.get()
        metadata = self.metadata_call + [
            ("username", current_context["username"]),
            ("authorization", current_context["token"]),
        ]
        response = await self.stub.SetObjectAttribute(request, metadata=metadata)
        return response.value, response.is_exception

    @grpc_aio_error_handler
    async def del_object_attribute(self, object_id: UUID, attribute: str) -> tuple[bytes, bool]:
        request = backend_pb2.DelObjectAttributeRequest(
            object_id=str(object_id),
            attribute=attribute,
        )
        current_context = session_var.get()
        metadata = self.metadata_call + [
            ("username", current_context["username"]),
            ("authorization", current_context["token"]),
        ]
        response = await self.stub.DelObjectAttribute(request, metadata=metadata)
        return response.value, response.is_exception

    @grpc_aio_error_handler
    async def get_object_properties(self, object_id: UUID) -> bytes:
        request = backend_pb2.GetObjectPropertiesRequest(
            object_id=str(object_id),
        )

        response = await self.stub.GetObjectProperties(request, metadata=self.metadata_call)
        return response.value

    @grpc_aio_error_handler
    async def update_object_properties(self, object_id: UUID, serialized_properties: bytes):
        request = backend_pb2.UpdateObjectPropertiesRequest(
            object_id=str(object_id),
            serialized_properties=serialized_properties,
        )
        await self.stub.UpdateObjectProperties(request, metadata=self.metadata_call)

    @grpc_aio_error_handler
    async def new_object_version(self, object_id: UUID) -> str:
        request = backend_pb2.NewObjectVersionRequest(
            object_id=str(object_id),
        )
        response = await self.stub.NewObjectVersion(request, metadata=self.metadata_call)
        return response.object_info

    @grpc_aio_error_handler
    async def consolidate_object_version(self, object_id: UUID):
        request = backend_pb2.ConsolidateObjectVersionRequest(
            object_id=str(object_id),
        )
        await self.stub.ConsolidateObjectVersion(request, metadata=self.metadata_call)

    @grpc_aio_error_handler
    async def proxify_object(self, object_id: UUID, new_object_id: UUID):
        request = backend_pb2.ProxifyObjectRequest(
            object_id=str(object_id),
            new_object_id=str(new_object_id),
        )
        await self.stub.ProxifyObject(request, metadata=self.metadata_call)

    @grpc_aio_error_handler
    async def change_object_id(self, object_id: UUID, new_object_id: UUID):
        request = backend_pb2.ChangeObjectIdRequest(
            object_id=str(object_id),
            new_object_id=str(new_object_id),
        )
        await self.stub.ChangeObjectId(request, metadata=self.metadata_call)

    @grpc_aio_error_handler
    async def send_objects(
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
        await self.stub.SendObjects(request, metadata=self.metadata_call)

    @grpc_aio_error_handler
    async def flush_all(self):
        await self.stub.FlushAll(empty_pb2.Empty())

    @grpc_aio_error_handler
    async def stop(self):
        await self.stub.Stop(empty_pb2.Empty())

    @grpc_aio_error_handler
    async def drain(self):
        await self.stub.Drain(empty_pb2.Empty())
