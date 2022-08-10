"""Initialization and finalization of dataClay client API.

The `init` and `finish` functions are availble through the
dataclay.api package.
"""

from dataclay.commonruntime.Settings import settings
from dataclay.communication.grpc.clients.ExecutionEnvGrpcClient import EEClient
from dataclay_common.protos.common_messages_pb2 import LANG_PYTHON
from dataclay.serialization.lib.SerializationLibUtils import (
    SerializationLibUtilsSingleton,
)
from dataclay.commonruntime.DataClayRuntime import DataClayRuntime
from dataclay.commonruntime.RuntimeType import RuntimeType
from dataclay.heap.ClientHeapManager import ClientHeapManager
from dataclay.loader.ClientObjectLoader import ClientObjectLoader

# Sentinel-like object to catch some typical mistakes
from dataclay.util.management.metadataservice.MetaDataInfo import MetaDataInfo
from dataclay.util.management.metadataservice.RegistrationInfo import RegistrationInfo
import traceback

from dataclay_common.managers.object_manager import ObjectMetadata

UNDEFINED_LOCAL = object()


class ClientRuntime(DataClayRuntime):

    current_type = RuntimeType.client

    def __init__(self):

        DataClayRuntime.__init__(self)

    def initialize_runtime_aux(self):
        self.dataclay_heap_manager = ClientHeapManager(self)
        self.dataclay_object_loader = ClientObjectLoader(self)

    def is_exec_env(self):
        return False

    def store_object(self, instance):
        raise RuntimeError("StoreObject can only be used from the ExecutionEnvironment")

    def make_persistent(self, instance, alias, backend_id, recursive):
        """This method creates a new Persistent Object using the provided stub
        instance and, if indicated, all its associated objects also Logic module API used for communication
        This function is called from a stub/execution class
        :param instance: Instance to make persistent
        :param backend_id: Indicates which is the destination backend
        :param recursive: Indicates if make persistent is recursive
        :param alias: Alias for the object
        :returns: ID of the backend in which te object was persisted.
        :type instance: DataClayObject
        :type backend_id: DataClayID
        :type recursive: boolean
        :type alias: string
        :rtype: DataClayID
        :raises RuntimeError: if backend id is UNDEFINED_LOCAL.
        """

        self.logger.debug(
            f"Starting make persistent object for instance with id {instance.get_object_id()}"
        )

        if backend_id is UNDEFINED_LOCAL:
            # This is a commonruntime end user pitfall,
            # @abarcelo thinks that it is nice
            # (and exceptionally detailed) error
            raise RuntimeError(
                """
                You are trying to use dataclay.api.LOCAL but either:
                  - dataClay has not been initialized properly
                  - LOCAL has been wrongly imported.
                
                Be sure to use LOCAL with:
                
                from dataclay import api
                
                and reference it with `api.LOCAL`
                
                Refusing the temptation to guess."""
            )
        location = instance.get_hint()
        if location is None:
            location = backend_id
            # Choose location if needed
            # If object is already persistent -> it must have a Hint (location = hint here)
            # If object is not persistent -> location is choosen (provided backend id or random, hash...).
            if location is None:
                location = self.choose_location(instance)

        if not instance.is_persistent():
            if alias is not None:
                # Add a new alias to an object.
                # Use cases:
                # 1 - object was persisted without alias and not yet registered -> we need to register it with new alias.
                # 2 - object was persisted and it is already registered -> we only add a new alias
                # 3 - object was persisted with an alias and it must be already registered -> we add a new alias.

                # From client side, we cannot check if object is registered or not (we do not have isPendingToRegister like EE)
                # Therefore, we call MetadataService with all information for registration.
                object_md = ObjectMetadata(
                    instance.get_object_id(),
                    alias,
                    instance.get_dataset_name(),
                    instance.get_class_extradata().class_id,
                    [location],
                    LANG_PYTHON,
                )
                # FIXME: The object registration should be done by execution environment.
                # So if the serialization fails, it is not stored. The client maybe can use
                # the update_object in order to change the alias or the is_read_only (to be decided)
                # self.ready_clients["@MDS"].register_object(self.get_session().id, object_md)

            # === MAKE PERSISTENT === #
            self.logger.debug(
                "Instance with object ID %s being send to EE", instance.get_object_id()
            )
            # set the default master location
            instance.set_master_location(location)
            instance.set_alias(alias)
            # We serialize objects like volatile parameters
            parameters = list()
            parameters.append(instance)
            params_order = list()
            params_order.append("object")
            params_spec = dict()
            params_spec["object"] = "DataClayObject"  # not used, see serialized_params_or_return
            serialized_objs = SerializationLibUtilsSingleton.serialize_params_or_return(
                params=parameters,
                iface_bitmaps=None,
                params_spec=params_spec,
                params_order=params_order,
                hint_volatiles=location,
                runtime=self,
                recursive=recursive,
            )

            # Avoid some race-conditions in communication (make persistent + execute where
            # execute arrives before).
            # TODO: fix volatiles under deserialization support for __setstate__ and __getstate__
            self.add_volatiles_under_deserialization(serialized_objs.vol_objs.values())

            # Get EE
            try:
                execution_client = self.ready_clients[location]
            except KeyError:
                exec_env = self.get_execution_environment_info(location)
                self.logger.debug(
                    "Not found in cache ExecutionEnvironment {%s}! Starting it at %s:%d",
                    location,
                    exec_env.hostname,
                    exec_env.port,
                )
                execution_client = EEClient(exec_env.hostname, exec_env.port)
                self.ready_clients[location] = execution_client

            # Call Execution Environment
            self.logger.verbose("Calling make persistent to EE %s ", location)
            execution_client.make_persistent(
                self.get_session().id, serialized_objs.vol_objs.values()
            )

            # update the hint with the location, and return it
            instance.set_hint(location)

            # remove volatiles under deserialization
            self.remove_volatiles_under_deserialization(serialized_objs.vol_objs.values())

        metadata_info = MetaDataInfo(
            instance.get_object_id(),
            False,
            instance.get_dataset_name(),
            instance.get_class_extradata().class_id,
            {location},
            alias,
            None,
        )
        self.metadata_cache[instance.get_object_id()] = metadata_info
        return location

    def add_session_reference(self, object_id):
        """
        @summary Add +1 reference associated to thread session
        @param object_id ID of object.
        """
        pass

    def execute_implementation_aux(self, operation_name, instance, parameters, exec_env_id=None):
        stub_info = instance.get_class_extradata().stub_info
        implementation_stub_infos = stub_info.implementations
        object_id = instance.get_object_id()

        self.logger.verbose(
            "Calling operation '%s' in object with ID %s", operation_name, object_id
        )
        self.logger.debug(
            "Call is being done into object with ID %s with #%d parameters",
            object_id,
            len(parameters),
        )

        using_hint = False
        if instance.get_hint() is not None:
            exec_env_id = instance.get_hint()
            self.logger.verbose("Using hint = %s", exec_env_id)
            using_hint = True
        else:
            exec_env_id = next(iter(self.get_metadata(object_id).locations))

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

    def delete_alias(self, dc_obj):
        session_id = self.get_session().id
        hint = dc_obj.get_hint()
        object_id = dc_obj.get_object_id()
        exec_location_id = hint
        if exec_location_id is None:
            exec_location_id = self.get_location(object_id)
        try:
            execution_client = self.ready_clients[exec_location_id]
        except KeyError:
            backend_to_call = self.get_execution_environment_info(exec_location_id)
            execution_client = EEClient(backend_to_call.hostname, backend_to_call.port)
            self.ready_clients[exec_location_id] = execution_client
        execution_client.delete_alias(session_id, object_id)
        dc_obj.set_alias(None)

    def close_session(self):
        self.logger.debug("** Closing session **")
        self.ready_clients["@MDS"].close_session(self.get_session().id)

    def get_hint(self):
        return None

    def get_session(self):
        return settings.current_session

    def synchronize(self, instance, operation_name, params):
        session_id = self.get_session().id
        object_id = instance.get_object_id()
        dest_backend_id = self.get_location(instance.get_object_id())
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
        execution_client.synchronize(session_id, object_id, implementation_id, serialized_params)

    def detach_object_from_session(self, object_id, hint):
        try:
            cur_session = self.get_session().id
            exec_location_id = hint
            if exec_location_id is None:
                exec_location_id = self.get_location(object_id)
            try:
                execution_client = self.ready_clients[exec_location_id]
            except KeyError:
                backend_to_call = self.get_execution_environment_info(exec_location_id)
                execution_client = EEClient(backend_to_call.hostname, backend_to_call.port)
                self.ready_clients[exec_location_id] = execution_client
            execution_client.detach_object_from_session(object_id, cur_session)
        except:
            traceback.print_exc()

    def federate_to_backend(self, dc_obj, external_execution_environment_id, recursive):
        object_id = dc_obj.get_object_id()
        hint = dc_obj.get_hint()
        session_id = self.get_session().id
        exec_location_id = hint
        if exec_location_id is None:
            exec_location_id = self.get_location(object_id)
        try:
            execution_client = self.ready_clients[exec_location_id]
        except KeyError:
            exec_env = self.get_execution_environment_info(exec_location_id)
            execution_client = EEClient(exec_env.hostname, exec_env.port)
            self.ready_clients[exec_location_id] = execution_client

        self.logger.debug(
            "[==FederateObject==] Starting federation of object by %s calling EE %s with dest dataClay %s, and session %s",
            object_id,
            exec_location_id,
            external_execution_environment_id,
            session_id,
        )
        execution_client.federate(
            session_id, object_id, external_execution_environment_id, recursive
        )

    def unfederate_from_backend(self, dc_obj, external_execution_environment_id, recursive):
        object_id = dc_obj.get_object_id()
        hint = dc_obj.get_hint()
        session_id = self.get_session().id
        self.logger.debug(
            "[==UnfederateObject==] Starting unfederation of object %s with ext backend %s, and session %s",
            object_id,
            external_execution_environment_id,
            session_id,
        )
        exec_location_id = hint
        if exec_location_id is None:
            exec_location_id = self.get_location(object_id)
        try:
            execution_client = self.ready_clients[exec_location_id]
        except KeyError:
            exec_env = self.get_execution_environment_info(exec_location_id)
            execution_client = EEClient(exec_env.hostname, exec_env.port)
            self.ready_clients[exec_location_id] = execution_client

        execution_client.unfederate(
            session_id, object_id, external_execution_environment_id, recursive
        )
