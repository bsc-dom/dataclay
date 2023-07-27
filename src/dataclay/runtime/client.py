""" ClientRuntime """

import io
import logging
import random
import traceback

from dataclay.dataclay_object import DataClayObject
from dataclay.exceptions import *
from dataclay.metadata.client import MetadataClient
from dataclay.runtime.runtime import DataClayRuntime
from dataclay.utils.pickle import RecursiveLocalPickler
from dataclay.utils.telemetry import trace

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

    def make_persistent(self, instance: DataClayObject, alias=None, backend_id=None):
        """This method creates a new Persistent Object using the provided stub
        instance and, if indicated, all its associated objects also Logic module API used for communication
        This function is called from a stub/execution class

        Args:
            instance: Instance to make persistent
            backend_id: Indicates which is the destination backend
            alias: Alias for the object

        Returns:
            ID of the backend in which the object was persisted.
        """
        logger.debug(f"Starting make persistent for object {instance._dc_id}")

        if instance._dc_is_registered:
            raise ObjectAlreadyRegisteredError(instance._dc_id)

        instance._dc_dataset_name = self.session.dataset_name
        if alias:
            self.metadata_service.new_alias(alias, self.session.dataset_name, instance._dc_id)
            # instance._dc_alias = alias

        if backend_id is None:
            self.update_backend_clients()
            backend_id, backend_client = random.choice(tuple(self.backend_clients.items()))

            # NOTE: Maybe use a quick update to avoid overhead.
            # Quiack_update only updates ee_infos, but don't check clients readiness
            # self.quick_update_backend_clients()
            # backend_id = random.choice(tuple(self.ee_infos.keys()))
            # backend_client = self.backend_clients[backend_id]
        else:
            backend_client = self.get_backend_client(backend_id)

        ######################################
        # Serialize instance with Pickle
        ######################################

        # TODO: Avoid some race-conditions in communication
        # (make persistent + execute where execute arrives before).
        # add_volatiles_under_deserialization and remove_volatiles_under_deserialization
        # TODO: Check if we can make a use of the recursive parameter

        f = io.BytesIO()
        serialized_local_dicts = []
        visited_objects = {instance._dc_id: instance}

        RecursiveLocalPickler(f, visited_objects, serialized_local_dicts).dump(instance._dc_dict)
        serialized_local_dicts.append(f.getvalue())
        backend_client.make_persistent(serialized_local_dicts)

        for dc_object in visited_objects.values():
            dc_object._clean_dc_properties()
            dc_object._dc_is_registered = True
            dc_object._dc_is_local = False
            dc_object._dc_is_loaded = False
            dc_object._dc_master_backend_id = backend_id

            self.add_to_heap(dc_object)

        return instance._dc_master_backend_id

    ############
    # Replicas #
    ############

    def synchronize(self, instance, operation_name, params):
        raise Exception("To refactor")
        dest_backend_id = self.get_hint()
        operation = self.get_operation_info(instance._dc_id, operation_name)
        implementation_id = self.get_implementation_id(instance._dc_id, operation_name)
        # === SERIALIZE PARAMETER ===
        serialized_params = SerializationLibUtilsSingleton.serialize_params_or_return(
            params=[params],
            iface_bitmaps=None,
            params_spec=operation.params,
            params_order=operation.paramsOrder,
            hint_volatiles=instance._dc_master_backend_id,
            runtime=self,
        )

        ee_client = self.get_backend_client(dest_backend_id)
        ee_client.synchronize(
            self.session.id, instance._dc_id, implementation_id, serialized_params
        )

    #####################
    # Garbage collector #
    #####################

    def detach_object_from_session(self, object_id, hint):
        try:
            if hint is None:
                instance = self.inmemory_objects[object_id]
                self.update_object_metadata(instance)
                hint = instance._dc_master_backend_id

            ee_client = self.get_backend_client(hint)
            ee_client.detach_object_from_session(object_id, self.session.id)
        except:
            traceback.print_exc()

    ##############
    # Federation #
    ##############

    def federate_to_backend(self, instance, external_execution_environment_id, recursive):
        hint = instance._dc_master_backend_id
        if hint is None:
            self.update_object_metadata(instance)
            hint = self.get_hint()

        ee_client = self.get_backend_client(hint)

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
        hint = instance._dc_master_backend_id
        if hint is None:
            self.update_object_metadata(instance)
            hint = self.get_hint()
        ee_client = self.get_backend_client(hint)

        ee_client.unfederate(
            self.session.id, instance._dc_id, external_execution_environment_id, recursive
        )

    ############
    # Shutdown #
    ############

    def stop(self):
        self.metadata_service.close_session(self.session.id)
        self.close_backend_clients()
        self.metadata_service.close()
