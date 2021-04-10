
""" Class description goes here. """
from dataclay.serialization.lib.ObjectWithDataParamOrReturn import ObjectWithDataParamOrReturn

"""Deserialization code related to DataClay objects

The code implemented in this module is (at "this moment") identical to the ones
implemented in the Java package client.CommonLib. Specifically, the deserialize*
functions are more or less adapted here.
"""

from io import BytesIO
import logging

from dataclay.exceptions.exceptions import InvalidPythonSignature
from dataclay.serialization.python.lang.IntegerWrapper import IntegerWrapper
from dataclay.serialization.python.lang.VLQIntegerWrapper import VLQIntegerWrapper
from dataclay.serialization.python.util.PyTypeWildcardWrapper import PyTypeWildcardWrapper
import dataclay.communication.grpc.messages.common.common_messages_pb2 as common_messages
from dataclay.communication.grpc.Utils import get_metadata

__author__ = 'Alex Barcelo <alex.barcelo@bsc.es>'
__copyright__ = '2015 Barcelona Supercomputing Center (BSC-CNS)'

logger = logging.getLogger(__name__)

class DeserializationLibUtils(object):
    def deserialize_params(self, serialized_params_or_return, iface_bitmaps,
            param_specs, params_order, runtime):
        return self.deserialize_params_or_return(serialized_params_or_return,
                            iface_bitmaps,
                            param_specs,
                            params_order, runtime)


    def _create_buffer_and_deserialize(self, io_file, instance, ifacebitmaps, metadata, cur_deser_python_objs):
        """
        @postcondition: Create buffer and deserialize
        @param obj_bytes: bytes to deserialize
        @param instance: Instance to deserialize
        @param ifacebitmaps: Map of bitmaps representing the interfaces to use
        @param metadata: object metadata
        @param cur_deser_python_objs: Currently deserialized Java objects
        """

        # TODO: obj_bytes is an io_file, use a buffer instead
        instance.deserialize(io_file, ifacebitmaps, metadata, cur_deser_python_objs)


    def deserialize_grpc_message_from_db(self, obj_bytes):
        """
        @postcondition: Deserialize grpc message from DB
        @param obj_bytes: object bytes
        @return grpc msg stored in db
        """
        msg = common_messages.PersistentObjectInDB()
        msg.ParseFromString(obj_bytes)
        return msg


    def deserialize_object_from_db(self, object_to_fill, object_bytes, runtime):
        """
        @postcondition: Deserialize object from bytes
        @param object_to_fill: object to fill
        @param object_bytes: Object bytes
        @param runtime: runtime
        """

        msg = self.deserialize_grpc_message_from_db(object_bytes)
        metadata = get_metadata(msg.metadata)
        self.deserialize_object_from_db_bytes_aux(object_to_fill, metadata, msg.data, runtime)


    def deserialize_object_from_db_bytes_aux(self, object_to_fill, metadata, data, runtime):
        """
        @postcondition: Deserialize object from bytes into instance provided
        @param metadata: object metadata
        @param data: Object data
        @param runtime: runtime
        """

        cur_deser_python_objs = dict()
        io_file = BytesIO(data)
        object_to_fill.set_loaded(True)
        object_to_fill.set_persistent(True)
        object_to_fill.set_original_object_id(metadata.orig_object_id)
        object_to_fill.set_origin_location(metadata.origin_location)
        object_to_fill.set_root_location(metadata.root_location)
        object_to_fill.set_replica_locations(metadata.replica_locations)
        object_to_fill.set_alias(metadata.alias)
        self._create_buffer_and_deserialize(io_file, object_to_fill, None, metadata, cur_deser_python_objs)
        io_file.close()
        """
        GARBAGE COLLECTOR RACE CONDITION
        ================================
        If some object was cleaned and removed from GC retained refs, it does NOT mean it was removed
        from Weak references map (Heap) because we will ONLY remove an entry in Heap if it is
        pointing to NULL, i.e. the Java GC removed it.
        So, if some execution is requested after we remove an entry from retained refs (we cleaned and send
        the object to disk), we check if the
        object is in Heap (see executeImplementation in DS) and therefore, we created a new reference
        making impossible for Java GC to clean the reference. We will add the object to retained references
        again once it is deserialized from DB.
        """
        runtime.add_to_heap(object_to_fill)

    def deserialize_objbytes_from_db_into_obj_data(self, object_id, obj_bytes_from_db, runtime):
        """
        @postcondition: Deserialize object from bytes into ObjectData and return it.
        @param object_id: ID of object
        @param obj_bytes_from_db: Object bytes
        @param runtime: Runtime to use
        @return object data (to send) of this object
        """
        logger.debug("OBJECT_ID %s, OBJ_BYTES %s", object_id, obj_bytes_from_db)

        msg = self.deserialize_grpc_message_from_db(obj_bytes_from_db)
        metadata = get_metadata(msg.metadata)
        obj_bytes = BytesIO(msg.data)

        logger.debug("METADATA %s and METADATA CLASS_ID %s", metadata, metadata[1][0])

        return ObjectWithDataParamOrReturn(object_id, metadata.tags_to_class_ids[0], metadata, obj_bytes)


    def deserialize_metadata_from_db(self, obj_bytes_from_db):
        """
        @postcondition: deserialize metadata from db (just metadata)
        @param obj_bytes_from_db: object bytes from db
        @return metadata of the object
        """
        msg = common_messages.PersistentObjectInDB()
        msg.ParseFromString(obj_bytes_from_db)
        metadata = get_metadata(msg.metadata)
        return metadata


    def deserialize_object_with_data_in_client(self, param_or_ret, instance, ifacebitmpas, runtime, owner_session_id):
        """
        @postcondition: Deserialize object into a memory instance. ALSO called from executeImplementation in case of 'executions during
        deserialization'. THIS FUNCTION SHOULD NEVER BE CALLED FROM CLIENT SIDE.
        @param param_or_ret: Param/return bytes and metadata
        @param instance: Object in which to deserialize data
        @param ifacebitmaps: Interface bitmaps
        @param runtime: the runtime
        @param owner_session_id: Can be None. ID of owner session of the object. Used for volatiles pending to register.
        """

        """ Lock object until deserialization is finished in case another instance is waiting to do the same so much """
        runtime.lock(instance.get_object_id())
        try:
            metadata = param_or_ret.metadata
            io_file = BytesIO(param_or_ret.obj_bytes)
            cur_deser_python_objs = dict()
            self._create_buffer_and_deserialize(io_file, instance, None, metadata, cur_deser_python_objs)
            io_file.close()
            instance.set_persistent(False)
            instance.set_hint(None)
            instance.set_original_object_id(metadata.orig_object_id)
            instance.set_origin_location(metadata.origin_location)
            instance.set_root_location(metadata.root_location)
            instance.set_replica_locations(metadata.replica_locations)
            instance.set_alias(metadata.alias)
        finally:
            runtime.unlock(instance.get_object_id())


    def deserialize_object_with_data(self, param_or_ret, instance, ifacebitmpas, runtime, owner_session_id, force_deserialization):
        """
        @postcondition: Deserialize object into a memory instance. ALSO called from executeImplementation in case of 'executions during
        deserialization'. THIS FUNCTION SHOULD NEVER BE CALLED FROM CLIENT SIDE.
        @param param_or_ret: Param/return bytes and metadata
        @param instance: Object in which to deserialize data
        @param ifacebitmaps: Interface bitmaps
        @param runtime: the runtime
        @param owner_session_id: Can be None. ID of owner session of the object. Used for volatiles pending to register.
        @param force_deserialization: Check if the object is loaded or not. If FALSE and loaded, then no deserialization is happening. If TRUE, then
        deserialization is forced.
        """

        """
        FORCE DESERIALIZATION NOTE.
        Volatiles in server can be created in two ways: received from client or in some execution.
        If created during execution, flag loaded = true, but if received, flag loaded should be false until
        the object is properly loaded. In order to control the first case, constructor of the object is
        setting loaded to true and here we set it to false. Therefore we need to "force" deserialization sometimes.
        Also happening in update of objects and cleaning in GC.
        """
        """ Lock object until deserialization is finished in case another instance is waiting to do the same so much """
        runtime.lock(instance.get_object_id())
        try:
            if force_deserialization or not instance.is_loaded():
                """ TODO: improve GRPC messages """
                metadata = param_or_ret.metadata
                io_file = BytesIO(param_or_ret.obj_bytes)
                cur_deser_python_objs = dict()
                self._create_buffer_and_deserialize(io_file, instance, None, metadata, cur_deser_python_objs)
                io_file.close()
                instance.set_loaded(True)
                instance.set_persistent(True)
                instance.set_original_object_id(metadata.orig_object_id)
                instance.set_origin_location(metadata.origin_location)
                instance.set_root_location(metadata.root_location)
                instance.set_replica_locations(metadata.replica_locations)
                instance.set_alias(metadata.alias)
                if owner_session_id is not None:
                        instance.set_owner_session_id(owner_session_id)

        finally:
            runtime.unlock(instance.get_object_id())


    def deserialize_return(self, serialized_params_or_return, iface_bitmaps, return_type, runtime):

        if serialized_params_or_return.num_params == 0:
            logger.verbose("No return to deserialize: returning None")
            return None
        return self.deserialize_params_or_return(serialized_params_or_return,
                            iface_bitmaps,
                            {"0": return_type},
                            ["0"], runtime)[0]


    def deserialize_params_or_return(self, serialized_params_or_return,
            iface_bitmaps, param_specs, params_order, runtime):
        """
        Deserialize parameters or return of an execution
        :param serialized_params_or_return: serialized parameters or return
        :param iface_bitmaps: interface bitmaps
        :param param_specs: specifications of parameters
        :param params_order: order of parameters
        :param runtime: runtime being used
        """
        num_params = serialized_params_or_return.num_params
        params = [None] * num_params

        """ VOLATILES """
        first_volatile = True
        for i, serialized_param in serialized_params_or_return.vol_objs.items():
            object_id = serialized_param.object_id
            class_id = serialized_param.class_id
            logger.verbose("Deserializing volatile with object ID %s" % str(object_id))

            if first_volatile:
                runtime.add_volatiles_under_deserialization(serialized_params_or_return.vol_objs.values())
                first_volatile = False

            deserialized_param = runtime.get_or_new_volatile_instance_and_load(object_id, class_id, runtime.get_hint(),
                                                                               serialized_param, iface_bitmaps)

            # For makePersistent or federate methods, we must know that there is a session using the object which
            # is the one that persisted/federated. Normally, we know a client is using an object if we serialize
            # it to send to him but in that case client has created/federated the object.
            runtime.add_session_reference(deserialized_param.get_object_id())

            if i < num_params:
                params[i] = deserialized_param

        """ LANGUAGE """
        for i, serialized_param in serialized_params_or_return.lang_objs.items():
            logger.verbose("Deserializing language type at index %s" % str(i))

            obj_bytes = BytesIO(serialized_param[1])
            params[i] = self.deserialize_language(obj_bytes, param_specs[params_order[i]])
            obj_bytes.close()

        """ IMMUTABLES """
        for i, serialized_param in serialized_params_or_return.imm_objs.items():
            logger.verbose("Deserializing immutable type at index %s" % str(i))

            obj_bytes = BytesIO(serialized_param)
            params[i] = self.deserialize_immutable(obj_bytes, param_specs[params_order[i]])
            obj_bytes.close()

        """ PERSISTENT """
        for i, serialized_param in serialized_params_or_return.persistent_refs.items():

            object_id = serialized_param.object_id
            hint = serialized_param.hint
            class_id = serialized_param.class_id

            logger.verbose("Deserializing persistent object with object ID %s" % str(object_id))

            deserialized_param = runtime.get_or_new_persistent_instance(object_id, class_id, hint)
            deserialized_param.set_persistent(True)
            if i < num_params:
                params[i] = deserialized_param
                # Set hint in metadata (ToDo: create general getOrNewInstance)

        if not first_volatile:
            runtime.remove_volatiles_under_deserialization()
        return params


    def deserialize_association(self, io_file, iface_bitmaps,
            metadata, cur_deserialized_objs, runtime):
        """
        @postcondition: deserialize association
        @param io_file: bytes of the object containing the association
        @param iface_bitmaps: interface bitmaps
        @param metadata: metadata of the object
        @param cur_deserialized_objs: current deserialized objects
        @param runtime: the runtime
        """
        tag = VLQIntegerWrapper().read(io_file)
        object_id = metadata.tags_to_oids[tag]
        metaclass_id = metadata.tags_to_class_ids[tag]
        # TODO: NumRefs ( metadata[3]) not deserialized?? Ask about
        # How/Where use NumRefs (metadata[3])?
        hint = None
        try:
            hint = metadata.tags_to_hints[tag]
        except KeyError:
            pass
        obj = runtime.get_or_new_persistent_instance(object_id, metaclass_id, hint)
        cur_deserialized_objs[tag] = obj
        return obj


    def deserialize_immutable(self, io_file, type_):
        # Well, if it is a primitive type we already have them...
        try:
            ptw = PyTypeWildcardWrapper(type_.signature)
        except InvalidPythonSignature:
            raise NotImplementedError("Only Java primitive types are "
                                          "understood in Python.")
        return ptw.read(io_file)


    def deserialize_language(self, io_file, type_):
        # Well, if it is a primitive type we already have them...
        try:
            ptw = PyTypeWildcardWrapper(type_.signature)
        except InvalidPythonSignature:
            raise NotImplementedError("In fact, InvalidPythonSignature was "
                                          "not even implemented, seems somebody is "
                                          "raising it without implementing logic.")
        return ptw.read(io_file)


    def extract_reference_counting(self, io_bytes):
        io_file = BytesIO(io_bytes)
        io_file.seek(0)
        ref_counting_pos = IntegerWrapper().read(io_file)
        io_file.seek(ref_counting_pos)
        # read up to last byte
        ref_bytes = io_file.read()
        io_file.close()
        return ref_bytes

DeserializationLibUtilsSingleton = DeserializationLibUtils()

class PersistentLoadPicklerHelper(object):
    """Helper to solve deserialization of associations inside Pickled structures.

    See https://docs.python.org/2.7/library/pickle.html#pickling-and-unpickling-external-objects
    for more information of what this is doing.

    The `__call__` method is being called by Pickle for persistent ids, i.e.,
    objects that have been serialized by PersistentIdPicklerHelper and thus
    are associations (DataClayObjects).

    The code is very close to the deserialize association.
    """

    def __init__(self, metadata, cur_deserialized_objs, runtime):
        self._metadata = metadata
        self._runtime = runtime
        self._cur_deserialized_objs = cur_deserialized_objs

    def __call__(self, str_tag):
        tag = int(str_tag)
        object_id = self._metadata.tags_to_oids[tag]
        metaclass_id = self._metadata.tags_to_class_ids[tag]

        # TODO: NumRefs ( metadata[3]) not deserialized?? Ask about
        # How/Where use NumRefs (metadata[3])?

        hint = None
        try:
            hint = self._metadata.tags_to_hints[tag]
        except KeyError:
            logger.debug("No Metadata Hints")
            pass
        obj = self._runtime.get_or_new_persistent_instance(object_id, metaclass_id, hint)
        self._cur_deserialized_objs[tag] = obj
        return obj
