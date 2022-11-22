"""Initialization and finalization of dataClay client API.

The `init` and `finish` functions are availble through the
dataclay.api package.
"""

import logging
import pickle
import traceback

from dataclay.runtime.dataclay_runtime import DataClayRuntime
from dataclay.serialization.lib.SerializationLibUtils import SerializationLibUtilsSingleton
from dataclay.backend.client import BackendClient
from dataclay.metadata.client import MetadataClient
from opentelemetry import trace

from dataclay.dataclay_object import DataClayObject

UNDEFINED_LOCAL = object()

tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)


class ClientRuntime(DataClayRuntime):

    session = None

    def __init__(self, metadata_service_host, metadata_service_port):
        # Initialize parent
        metadata_service = MetadataClient(metadata_service_host, metadata_service_port)
        super().__init__(metadata_service)

    def add_to_heap(self, instance: DataClayObject):
        self.inmemory_objects[instance._dc_id] = instance

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
            ID of the backend in which the object was persisted.
        """

        if instance._dc_is_persistent:
            raise RuntimeError("Instance is already persistent")
        else:
            logger.debug(f"Starting make persistent for object {instance._dc_id}")

            instance._dc_alias = alias
            instance._dc_master_ee_id = backend_id or self.get_backend_id_by_object_id(
                instance._dc_id
            )

            # Gets Execution Environment client
            try:
                ee_client = self.backend_clients[instance._dc_master_ee_id]
            except KeyError:
                logger.debug(f"Client {instance._dc_master_ee_id} not found in cache!")
                exec_env = self.get_execution_environment_info(instance._dc_master_ee_id)
                ee_client = BackendClient(exec_env.hostname, exec_env.port)
                self.backend_clients[instance._dc_master_ee_id] = ee_client

            ######################################
            # Serialize instance with Pickle
            ######################################

            # TODO: Improve it with a single make_persistent call to ee of all
            # dc objects, instead of one call per object
            # TODO: Avoid some race-conditions in communication
            # (make persistent + execute where execute arrives before).
            # add_volatiles_under_deserialization and remove_volatiles_under_deserialization
            # TODO: Check if we can make a use of the recursive parameter

            # Must be set to True before pickle.dumps to avoid infinit recursion
            instance._dc_is_persistent = True

            serialized_dict = pickle.dumps(instance.__dict__)
            ee_client.new_make_persistent(self.session.id, serialized_dict)

            return instance._dc_master_ee_id

    # NOTE: This function may be removed.
    # When an alias is removed without having the instance, the persistent object
    # has to know it if we consult its alias, therefore, in all cases, the alias
    # will have to be updated from the single source of truth i.e. the etcd metadata
    def delete_alias(self, instance):
        ee_id = instance._dc_master_ee_id
        if not ee_id:
            self.update_object_metadata(instance)
            ee_id = self.get_hint()
        try:
            ee_client = self.backend_clients[ee_id]
        except KeyError:
            ee_info = self.get_execution_environment_info(ee_id)
            ee_client = BackendClient(ee_info.hostname, ee_info.port)
            self.backend_clients[ee_id] = ee_client
        ee_client.delete_alias(self.session.id, instance._dc_id)
        instance._dc_alias = None

    def close_session(self):
        self.metadata_service.close_session(self.session.id)

    def get_hint(self):
        return None

    def synchronize(self, instance, operation_name, params):
        dest_backend_id = self.get_hint()
        operation = self.get_operation_info(instance._dc_id, operation_name)
        implementation_id = self.get_implementation_id(instance._dc_id, operation_name)
        # === SERIALIZE PARAMETER ===
        serialized_params = SerializationLibUtilsSingleton.serialize_params_or_return(
            params=[params],
            iface_bitmaps=None,
            params_spec=operation.params,
            params_order=operation.paramsOrder,
            hint_volatiles=instance._dc_master_ee_id,
            runtime=self,
        )
        try:
            ee_client = self.backend_clients[dest_backend_id]
        except KeyError:
            exec_env = self.get_execution_environment_info(dest_backend_id)
            ee_client = BackendClient(exec_env.hostname, exec_env.port)
            self.backend_clients[dest_backend_id] = ee_client
        ee_client.synchronize(
            self.session.id, instance._dc_id, implementation_id, serialized_params
        )

    def detach_object_from_session(self, object_id, hint):
        try:
            if hint is None:
                instance = self.inmemory_objects[object_id]
                self.update_object_metadata(instance)
                hint = instance._dc_master_ee_id
            try:
                ee_client = self.backend_clients[hint]
            except KeyError:
                ee_info = self.get_execution_environment_info(hint)
                ee_client = BackendClient(ee_info.hostname, ee_info.port)
                self.backend_clients[hint] = ee_client
            ee_client.detach_object_from_session(object_id, self.session.id)
        except:
            traceback.print_exc()

    def federate_to_backend(self, instance, external_execution_environment_id, recursive):
        hint = instance._dc_master_ee_id
        if hint is None:
            self.update_object_metadata(instance)
            hint = self.get_hint()
        try:
            ee_client = self.backend_clients[hint]
        except KeyError:
            exec_env = self.get_execution_environment_info(hint)
            ee_client = BackendClient(exec_env.hostname, exec_env.port)
            self.backend_clients[hint] = ee_client

        logger.debug(
            "[==FederateObject==] Starting federation of object by %s calling EE %s with dest dataClay %s, and session %s",
            instance._dc_id,
            hint,
            external_execution_environment_id,
            self.session.id,
        )
        ee_client.federate(
            self.session.id, instance._dc_id, external_execution_environment_id, recursive
        )

    def unfederate_from_backend(self, instance, external_execution_environment_id, recursive):
        logger.debug(
            "[==UnfederateObject==] Starting unfederation of object %s with ext backend %s, and session %s",
            instance._dc_id,
            external_execution_environment_id,
            self.session.id,
        )
        hint = instance._dc_master_ee_id
        if hint is None:
            self.update_object_metadata(instance)
            hint = self.get_hint()
        try:
            ee_client = self.backend_clients[hint]
        except KeyError:
            exec_env = self.get_execution_environment_info(hint)
            ee_client = BackendClient(exec_env.hostname, exec_env.port)
            self.backend_clients[hint] = ee_client

        ee_client.unfederate(
            self.session.id, instance._dc_id, external_execution_environment_id, recursive
        )
