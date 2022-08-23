"""Initialization and finalization of dataClay client API.

The `init` and `finish` functions are availble through the
dataclay.api package.
"""

import logging
import traceback

from dataclay.commonruntime.DataClayRuntime import DataClayRuntime
from dataclay.commonruntime.Settings import settings
from dataclay.communication.grpc.clients.ExecutionEnvGrpcClient import EEClient
from dataclay.heap.ClientHeapManager import ClientHeapManager
from dataclay.loader.ClientObjectLoader import ClientObjectLoader
from dataclay.serialization.lib.SerializationLibUtils import SerializationLibUtilsSingleton
from dataclay.util.management.metadataservice.MetaDataInfo import MetaDataInfo
from dataclay.util.management.metadataservice.RegistrationInfo import RegistrationInfo
from dataclay_common.clients.metadata_service_client import MDSClient
from dataclay_common.protos.common_messages_pb2 import LANG_PYTHON

UNDEFINED_LOCAL = object()

logger = logging.getLogger(__name__)


class ClientRuntime(DataClayRuntime):

    metadata_service = None
    dataclay_heap_manager = None
    dataclay_object_loader = None
    session = None

    def __init__(self, metadata_service_host, metadata_service_port):
        DataClayRuntime.__init__(self)
        self.metadata_service = MDSClient(metadata_service_host, metadata_service_port)
        self.dataclay_heap_manager = ClientHeapManager(self)
        self.dataclay_object_loader = ClientObjectLoader(self)
        self.dataclay_heap_manager.start()

    def is_client(self):
        return True

    def make_persistent(self, instance, alias, backend_id, recursive):
        """This method creates a new Persistent Object using the provided stub
        instance and, if indicated, all its associated objects also Logic module API used for communication
        This function is called from a stub/execution class

        Args:
            instance: Instance to make persistent
            backend_id: Indicates which is the destination backend
            recursive: Indicates if make persistent is recursive
            alias: Alias for the object

        Returns:
            ID of the backend in which te object was persisted.
        """

        if instance.is_persistent():
            raise RuntimeError("Instance is already persistent")
        else:
            logger.debug(f"Starting make persistent for object {instance.get_object_id()}")

            if not instance.get_hint():
                instance.set_hint(
                    backend_id or self.get_backend_by_object_id(instance.get_object_id())
                )

            logger.debug(f"Sending object {instance.get_object_id()} to EE")

            # sets the default master location
            instance.set_master_location(instance.get_hint())
            instance.set_alias(alias)

            # serializes objects like volatile parameters
            serialized_objs = SerializationLibUtilsSingleton.serialize_params_or_return(
                params=[instance],
                iface_bitmaps=None,
                params_spec={"object": "DataClayObject"},
                params_order=["object"],
                hint_volatiles=instance.get_hint(),
                runtime=self,
                recursive=recursive,
            )

            # Avoid some race-conditions in communication (make persistent + execute where execute arrives before).
            # TODO: fix volatiles under deserialization support for __setstate__ and __getstate__
            self.add_volatiles_under_deserialization(serialized_objs.vol_objs.values())

            # Gets EE Client
            try:
                execution_client = self.ready_clients[instance.get_hint()]
            except KeyError:
                exec_env = self.get_execution_environment_info(instance.get_hint())
                logger.debug(
                    f"ExecutionEnvironment {instance.get_hint()} not found in cache! Starting it at {exec_env.hostname}:{exec_env.port}",
                )
                execution_client = EEClient(exec_env.hostname, exec_env.port)
                self.ready_clients[instance.get_hint()] = execution_client

            logger.verbose(f"Calling make persistent to EE {instance.get_hint()}")
            execution_client.make_persistent(self.session.id, serialized_objs.vol_objs.values())

            # removes volatiles under deserialization
            self.remove_volatiles_under_deserialization(serialized_objs.vol_objs.values())

            # TODO: Use ObjectMD instead ?
            metadata_info = MetaDataInfo(
                instance.get_object_id(),
                False,
                instance.get_dataset_name(),
                instance.get_class_extradata().class_id,
                {instance.get_hint()},
                alias,
                None,
            )

            self.metadata_cache[instance.get_object_id()] = metadata_info
            return instance.get_hint()

    def execute_implementation_aux(self, operation_name, instance, parameters, exec_env_id=None):
        object_id = instance.get_object_id()

        logger.debug(
            f"Calling operation {operation_name} in object {object_id} with parameters {parameters}"
        )

        using_hint = True
        exec_env_id = instance.get_hint()
        if exec_env_id is None:
            exec_env_id = next(iter(self.get_metadata(object_id).locations))
            using_hint = False

        return self.call_execute_to_ds(
            instance, parameters, operation_name, exec_env_id, using_hint
        )

    def get_operation_info(self, object_id, operation_name):
        dcc_extradata = self.get_object_by_id(object_id).get_class_extradata()
        stub_info = dcc_extradata.stub_info
        implementation_stub_infos = stub_info.implementations
        operation = implementation_stub_infos[operation_name]
        return operation

    def get_implementation_id(self, object_id, operation_name, implementation_idx=0):
        operation = self.get_operation_info(object_id, operation_name)
        return operation.remoteImplID

    # NOTE: This function may be removed.
    # When an alias is removed without having the instance, the persistent object
    # has to know it if we consult its alias, therefore, in all cases, the alias
    # will have to be updated from the single source of truth i.e. the etcd metadata
    def delete_alias(self, instance):
        ee_id = instance.get_hint()
        if not ee_id:
            self.update_object_metadata(instance)
            ee_id = self.get_hint()
        try:
            ee_client = self.ready_clients[ee_id]
        except KeyError:
            ee_info = self.get_execution_environment_info(ee_id)
            ee_client = EEClient(ee_info.hostname, ee_info.port)
            self.ready_clients[ee_id] = ee_client
        ee_client.delete_alias(self.session.id, instance.get_object_id())
        instance.set_alias(None)

    def close_session(self):
        self.metadata_service.close_session(self.session.id)

    def get_hint(self):
        return None

    def synchronize(self, instance, operation_name, params):
        dest_backend_id = self.get_hint()
        operation = self.get_operation_info(instance.get_object_id(), operation_name)
        implementation_id = self.get_implementation_id(instance.get_object_id(), operation_name)
        # === SERIALIZE PARAMETER ===
        serialized_params = SerializationLibUtilsSingleton.serialize_params_or_return(
            params=[params],
            iface_bitmaps=None,
            params_spec=operation.params,
            params_order=operation.paramsOrder,
            hint_volatiles=instance.get_hint(),
            runtime=self,
        )
        try:
            execution_client = self.ready_clients[dest_backend_id]
        except KeyError:
            exec_env = self.get_execution_environment_info(dest_backend_id)
            execution_client = EEClient(exec_env.hostname, exec_env.port)
            self.ready_clients[dest_backend_id] = execution_client
        execution_client.synchronize(
            self.session.id, instance.get_object_id(), implementation_id, serialized_params
        )

    def detach_object_from_session(self, object_id, hint):
        try:
            if hint is None:
                instance = self.get_from_heap(object_id)
                self.update_object_metadata(instance)
                hint = instance.get_hint()
            try:
                ee_client = self.ready_clients[hint]
            except KeyError:
                ee_info = self.get_execution_environment_info(hint)
                ee_client = EEClient(ee_info.hostname, ee_info.port)
                self.ready_clients[hint] = ee_client
            ee_client.detach_object_from_session(object_id, self.session.id)
        except:
            traceback.print_exc()

    def federate_to_backend(self, instance, external_execution_environment_id, recursive):
        hint = instance.get_hint()
        if hint is None:
            self.update_object_metadata(instance)
            hint = self.get_hint()
        try:
            execution_client = self.ready_clients[hint]
        except KeyError:
            exec_env = self.get_execution_environment_info(hint)
            execution_client = EEClient(exec_env.hostname, exec_env.port)
            self.ready_clients[hint] = execution_client

        logger.debug(
            "[==FederateObject==] Starting federation of object by %s calling EE %s with dest dataClay %s, and session %s",
            instance.get_object_id(),
            hint,
            external_execution_environment_id,
            self.session.id,
        )
        execution_client.federate(
            self.session.id, instance.get_object_id(), external_execution_environment_id, recursive
        )

    def unfederate_from_backend(self, instance, external_execution_environment_id, recursive):
        logger.debug(
            "[==UnfederateObject==] Starting unfederation of object %s with ext backend %s, and session %s",
            instance.get_object_id(),
            external_execution_environment_id,
            self.session.id,
        )
        hint = instance.get_hint()
        if hint is None:
            self.update_object_metadata(instance)
            hint = self.get_hint()
        try:
            execution_client = self.ready_clients[hint]
        except KeyError:
            exec_env = self.get_execution_environment_info(hint)
            execution_client = EEClient(exec_env.hostname, exec_env.port)
            self.ready_clients[hint] = execution_client

        execution_client.unfederate(
            self.session.id, instance.get_object_id(), external_execution_environment_id, recursive
        )
