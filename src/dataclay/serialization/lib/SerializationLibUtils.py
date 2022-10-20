"""Serialization code related to DataClay objects

The code implemented in this module is (at "this moment") identical to the ones
implemented in the Java package client.CommonLib. Specifically, the serialize*
functions are more or less adapted here.
"""
import logging
from io import BytesIO

import dataclay_common.protos.common_messages_pb2 as common_messages

import dataclay
from dataclay.communication.grpc.Utils import get_metadata
from dataclay.exceptions.exceptions import InvalidPythonSignature
from dataclay.serialization.lib.ObjectWithDataParamOrReturn import ObjectWithDataParamOrReturn
from dataclay.serialization.lib.PersistentParamOrReturn import PersistentParamOrReturn
from dataclay.serialization.lib.SerializedParametersOrReturn import SerializedParametersOrReturn
from dataclay.serialization.python.lang.VLQIntegerWrapper import VLQIntegerWrapper
from dataclay.serialization.python.util.PyTypeWildcardWrapper import (PyTypeWildcardWrapper,
                                                                      safe_wait_if_compss_future)
from dataclay.util.DataClayObjectMetaData import DataClayObjectMetaData
from dataclay.util.IdentityDict import IdentityDict
from dataclay.util.ReferenceCounting import ReferenceCounting

__author__ = "Alex Barcelo <alex.barcelo@bsc.es>"
__copyright__ = "2015 Barcelona Supercomputing Center (BSC-CNS)"

logger = logging.getLogger(__name__)


class SerializationLibUtils(object):
    def _create_buffer_and_serialize(
        self,
        instance,
        ignore_user_types,
        ifacebitmaps,
        cur_serialized_objs,
        pending_objs,
        reference_counting,
        return_none_if_no_ref_counting=False,
    ):
        """
        @postcondition: Create buffer and serialize. TODO: modify buffer
        @param instance: Instance to serialize
        @param ignore_user_types: Indicates if user types found during serialization must be ignored or not
        @param ifacebitmaps: Map of bitmaps representing the interfaces to use
        @param cur_serialized_objs: Current serialized objects Object -> OID tag. This structure must be different during each serialization since OID
                tags are not shared.
        @param pending_objs: pending objects
        @param reference_counting: reference counting
        @param return_none_if_no_ref_counting: If true, return null if object does not reference any other object except language object. This is useful during
                   GC of not dirty objects without references.
        @return serialized bytes
        """

        buffer = BytesIO()
        instance.serialize(
            buffer, ignore_user_types, None, cur_serialized_objs, pending_objs, reference_counting
        )
        if return_none_if_no_ref_counting:
            if reference_counting.has_no_references():
                return None
        metadata = self.create_metadata(
            cur_serialized_objs,
            None,
            0,
            instance.get_original_object_id(),
            instance.get_root_location(),
            instance.get_origin_location(),
            instance.get_replica_locations(),
            instance.get_alias(),
            instance.is_read_only(),
            instance.get_dataset_name(),
        )
        dcc_extradata = instance.get_class_extradata()
        byte_array = buffer.getvalue()
        buffer.close()
        return ObjectWithDataParamOrReturn(
            instance.get_object_id(), dcc_extradata.class_id, metadata, byte_array
        )

    def serialize_association(
        self,
        io_output,  # final DataClayByteBuffer
        element,  # final DataClayObject
        cur_serialized_objs,  # final IdentityHashMap<Object, Integer>
        pending_objs,  # ListIterator<DataClayObject>
        reference_counting,
    ):
        try:
            tag = cur_serialized_objs[element]
        except KeyError:
            logger.debug("Adding object %s to pending_objects", element.get_object_id())

            pending_objs.append(element)
            tag = len(cur_serialized_objs)
            cur_serialized_objs[element] = tag

        """ update reference counting """
        associated_oid = element.get_object_id()
        hint = element.get_hint()
        reference_counting.increment_reference_counting(associated_oid, hint)

        """ write tag """
        VLQIntegerWrapper().write(io_output, tag)

    def serialize_params_or_return(
        self,
        params,
        iface_bitmaps,
        params_spec,
        params_order,
        hint_volatiles,
        runtime,
        recursive=True,
        for_update=False,
    ):

        """
        @postcondition: serialize parameters or return
        @param params: param
        :returns: serialized params [0: num_params, 1: imm_objs, 2: lang_objs, 3: vol_params, 4:pers_params] with following structure
            imm_objs is a dict of idx -> bytes
            lang_objs is a dict of idx -> bytes
            vol_params is a dict of object id -> [0: object id, 1: class id, 2: metadata, 3: bytes]
            pers_params is a dict of object id -> [0: oid, 1: hint, 2: class_id, 3:False ]
        """

        pending_objects = list()
        already_serialized_params = set()

        imm_objs = dict()
        lang_objs = dict()
        vol_params = dict()
        pers_params = dict()

        i = 0
        num_params = 0
        if params_order is not None:
            num_params = len(params_order)
        if num_params > 0:
            for param_name in params_order:

                param = params[i]
                if param is not None:
                    param = safe_wait_if_compss_future(param)

                    try:
                        oid = param.get_object_id()

                        runtime.add_session_reference(oid)

                        if param.is_persistent():
                            logger.debug("Serializing persistent parameter/return with oid %s", oid)

                            class_id = param.get_class_extradata().class_id
                            hint = param.get_hint()

                            pers_param = PersistentParamOrReturn(oid, hint, class_id)
                            pers_params[i] = pers_param

                        else:
                            logger.debug("Serializing volatile parameter/return with oid %s", oid)

                            # this is no-exception flow which means...
                            # ... means that it is a volatile object to serialize, with its OID
                            already_serialized_params.add(oid)
                            obj_with_data = self.serialize_dcobj_with_data(
                                param,  # final DataClayObject
                                pending_objects,  # final ListIterator<DataClayObject>
                                not recursive,
                                hint_volatiles,
                                runtime,
                                True,
                                for_update,
                            )

                            vol_params[i] = obj_with_data

                    except AttributeError:
                        try:
                            # ToDo: support for notifications (which is said to leave params_spec None)

                            param_type = params_spec[param_name]
                            ptw = PyTypeWildcardWrapper(param_type.signature)
                        except InvalidPythonSignature:
                            raise NotImplementedError(
                                "In fact, InvalidPythonSignature was "
                                "not even implemented, seems somebody is "
                                "raising it without implementing logic."
                            )
                        else:
                            io_output = BytesIO()
                            ptw.write(io_output, param)
                            imm_objs[i] = io_output.getvalue()
                            io_output.close()
                i = i + 1

            if recursive:
                while pending_objects:
                    # Note that pending objects are *only* DataClay Objects)
                    pending_obj = pending_objects.pop()
                    oid = pending_obj.get_object_id()

                    if oid in already_serialized_params:
                        continue

                    if pending_obj.is_persistent():
                        logger.debug(
                            "Serializing sub-object persistent parameter/return with oid %s", oid
                        )

                        class_id = param.get_class_extradata().class_id
                        hint = param.get_hint()

                        pers_param = PersistentParamOrReturn(oid, hint, class_id)
                        pers_params[i] = pers_param
                    else:
                        logger.debug(
                            "Serializing sub-object volatile parameter/return with oid %s", oid
                        )

                        obj_with_data = self.serialize_dcobj_with_data(
                            pending_obj,
                            pending_objects,
                            not recursive,
                            hint_volatiles,
                            runtime,
                            True,
                            for_update,
                        )

                        vol_params[i] = obj_with_data

                    # Ensure that it is put inside
                    already_serialized_params.add(oid)
                    i += 1
        else:
            logger.debug("Call with no parameters, no serialization required")

        serialized_params = SerializedParametersOrReturn(
            num_params=num_params,
            imm_objs=imm_objs,
            lang_objs=lang_objs,
            vol_objs=vol_params,
            pers_objs=pers_params,
        )
        return serialized_params

    def serialize_dcobj_with_data(
        self,
        dc_object,
        pending_objs,
        ignore_user_types,
        hint,
        runtime,
        force_pending_to_register,
        for_update=False,
    ):

        """
        @postcondition: Serialize DataClayObject with data.
        @param dc_object: DCObject
        @param ignore_user_types: Indicates if user types inside the instance must be ignored or not
        @param pending_objs: pending objects
        @param hint: Hint to set if needed
        @param runtime; Runtime managed
        @param force_pending_to_register: If TRUE, object is going to be set as pending to register. Take into account that this function is also called to
            serialize objects in 'moves','replicas',... and in that case this parameter must be FALSE to avoid overriding the
            actual value of the instance (actual pending or not).
        @param for_update whether this serialziation comes from an update operation or not
        """

        object_with_data = None
        object_id = dc_object.get_object_id()
        runtime.lock(object_id)
        try:
            cur_serialized_objs = IdentityDict()
            reference_counting = ReferenceCounting()
            cur_serialized_objs[dc_object] = 0
            """ Set flags of volatile/persisted obj. being send """
            # Set Hint in object being send/persisted. Hint provided during creation of metadata
            # is for associated objects that are not persistent yet (currently being persisted)
            # This algorithm can be improved in both languages, Python and Java.
            if for_update is False:
                dc_object.set_hint(hint)
                dc_object.set_persistent(True)

            object_with_data = self._create_buffer_and_serialize(
                dc_object,
                ignore_user_types,
                None,
                cur_serialized_objs,
                pending_objs,
                reference_counting,
            )

            if force_pending_to_register:
                dc_object.set_pending_to_register(True)

        finally:
            runtime.unlock(object_id)
        return object_with_data

    def create_metadata(
        self,
        cur_ser_objs,
        hint_for_missing,
        num_refs_pointing_to_obj,
        orig_object_id,
        root_location,
        origin_location,
        replica_locs,
        alias,
        is_read_only,
        dataset_name,
    ):

        # Prepare metadata structure

        tags_to_oids = dict()
        tags_to_class_id = dict()
        tags_to_hint = dict()

        for k, v in cur_ser_objs.items():
            from dataclay import DataClayObject

            if isinstance(k, DataClayObject):

                obj = k
                tag = v
                class_id = obj.get_class_extradata().class_id
                object_id = obj.get_object_id()
                hint = obj.get_hint()

                tags_to_oids[tag] = object_id
                tags_to_class_id[tag] = class_id
                logger.trace(
                    "[==Object Metadata==] Adding metadata tag %s -> oid %s", tag, object_id
                )
                logger.trace(
                    "[==Object Metadata==] Adding metadata tag %s -> class id %s", tag, class_id
                )

                if hint is not None:
                    logger.debug("[==Hint==] Setting hint %s association for tag %s", hint, tag)
                    tags_to_hint[tag] = hint
                else:
                    if hint_for_missing is not None:
                        logger.debug(
                            "[==Hint==] Setting hint %s association for tag %s",
                            hint_for_missing,
                            tag,
                        )
                        tags_to_hint[tag] = hint_for_missing

        response = DataClayObjectMetaData(
            alias,
            is_read_only,
            tags_to_oids,
            tags_to_class_id,
            tags_to_hint,
            num_refs_pointing_to_obj,
            orig_object_id,
            root_location,
            origin_location,
            replica_locs,
            dataset_name,
        )

        return response

    def serialize_for_db(self, object_id, metadata, object_bytes, is_store):
        """
        @postcondition: serialize object for DB store or update
        @param object_id: id of the object to store or update
        @param object_bytes: object bytes
        @param is_store: indicates if it is for a store in DB
        @return serialized msg
        """

        msg = common_messages.PersistentObjectInDB(
            data=object_bytes, metadata=get_metadata(metadata)
        )
        msgstr = msg.SerializeToString()
        return msgstr

    def serialize_for_db_gc(
        self, instance, ignore_user_types, ifacebitmaps, return_none_if_no_ref_counting=False
    ):
        """
        @postcondition: Serialize for flushing from GC
        @param instance: Instance to serialize
        @param ignore_user_types:Indicates if user types must be ignored
        @param ifacebitmaps: Interface bitmaps
        @param return_none_if_no_ref_counting: If true, return null if object does not reference any other object except language object. This is useful during
                   GC of not dirty objects without references.
        @return serialized bytes
        """

        cur_serialized_objs = IdentityDict()
        reference_counting = ReferenceCounting()
        pending_objs = list()
        cur_serialized_objs[instance] = 0
        obj_data = self._create_buffer_and_serialize(
            instance,
            ignore_user_types,
            ifacebitmaps,
            cur_serialized_objs,
            pending_objs,
            reference_counting,
            return_none_if_no_ref_counting=return_none_if_no_ref_counting,
        )
        if return_none_if_no_ref_counting:
            if obj_data == None:
                return None
        return self.serialize_for_db(
            instance.get_object_id(), obj_data.metadata, obj_data.obj_bytes, False
        )

    def serialize_for_db_gc_not_dirty(
        self, instance, ignore_user_types, ifacebitmaps, return_none_if_no_ref_counting=True
    ):
        """
        @postcondition: Serialize for flushing from GC not-dirty objects
        @param instance: Instance to serialize
        @param ignore_user_types:Indicates if user types must be ignored
        @param ifacebitmaps: Interface bitmaps
        @param return_none_if_no_ref_counting: If true, return null if object does not reference any other object except language object. This is useful during
                   GC of not dirty objects without references.
        @return serialized bytes
        """

        cur_serialized_objs = IdentityDict()
        reference_counting = ReferenceCounting()
        pending_objs = list()
        cur_serialized_objs[instance] = 0
        obj_data = self._create_buffer_and_serialize(
            instance,
            ignore_user_types,
            ifacebitmaps,
            cur_serialized_objs,
            pending_objs,
            reference_counting,
            return_none_if_no_ref_counting=return_none_if_no_ref_counting,
        )
        if return_none_if_no_ref_counting:
            if obj_data == None:
                return None
        return obj_data.obj_bytes


SerializationLibUtilsSingleton = SerializationLibUtils()


class PersistentIdPicklerHelper(object):
    """Helper to solve serialization of associations inside Pickled structures.

    See https://docs.python.org/2.7/library/pickle.html#pickling-and-unpickling-external-objects
    for more information of what this is doing. Note that the `__call__` is
    being called by Pickle for every object, and when we find a DataClayObject
    there, we proceed to do something very close to the serialize_association
    procedure.
    """

    def __init__(self, cur_serialized_objs, pending_objs, reference_counting):
        self._cur_serialized_objs = cur_serialized_objs
        self._pending_objs = pending_objs
        self._reference_counting = reference_counting

    def __call__(self, obj):
        if isinstance(obj, dataclay.DataClayObject):
            try:
                tag = self._cur_serialized_objs[obj]
            except KeyError:
                self._pending_objs.append(obj)
                tag = len(self._cur_serialized_objs)
                self._cur_serialized_objs[obj] = tag

            """ update reference counting """
            associated_oid = obj.get_object_id()
            hint = obj.get_hint()
            self._reference_counting.increment_reference_counting(associated_oid, hint)

            return str(tag)
