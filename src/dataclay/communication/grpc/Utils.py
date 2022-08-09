""" Class description goes here. """
from dataclay.serialization.lib.ObjectWithDataParamOrReturn import ObjectWithDataParamOrReturn
from dataclay.serialization.lib.PersistentParamOrReturn import PersistentParamOrReturn
from dataclay.serialization.lib.SerializedParametersOrReturn import SerializedParametersOrReturn
from dataclay.util.DataClayObjectMetaData import DataClayObjectMetaData
from dataclay.util.management.metadataservice.DataClayInstance import DataClayInstance
from dataclay.util.management.metadataservice.ExecutionEnvironment import ExecutionEnvironment
from dataclay.util.management.metadataservice.MetaDataInfo import MetaDataInfo
from dataclay.util.management.metadataservice.StorageLocation import StorageLocation

"""Utility methods for gRPC clients/server."""

import logging
import sys
import traceback
import uuid
import six

from dataclay_common.protos import common_messages_pb2 as common_messages

__author__ = "Enrico La Sala <enrico.lasala@bsc.es>"
__copyright__ = "2017 Barcelona Supercomputing Center (BSC-CNS)"

logger = logging.getLogger(__name__)


def get_credential(cred):
    """Get the pwdCredential of the corresponding protobuf message.

    :param cred: PasswordCredential/Credential protobuf message.
    :return: Depends on the param can return a Credential protobuf message or a PasswordCredential.
    """
    if cred is common_messages.Credential:
        if cred is None:
            return None
        else:
            return cred.password
    else:
        if cred is None:
            return common_messages.Credential()
        else:
            return common_messages.Credential(password=cred[1])


def get_msg_id(id):
    if id is None:
        return None
    return str(id)


def get_id(id_msg):
    """Create the ID based on protobuf message.

    :param id_msg: Common protobuf message.

    :return: UUID based on param.
    """
    if id_msg is None:
        return None
    elif id_msg == "":
        return None
    else:
        return uuid.UUID(id_msg)


def get_id_from_uuid(msg_str):
    """Create the ID based on id message.

    :param msg_str: string UUID.

    :return: Correct UUID.
    """
    if msg_str is None or msg_str == "":
        return None
    else:
        return uuid.UUID(msg_str)


def get_metadata(metadata):
    """Get Metadata GRPC message from DataclayMetaData.

    :param metadata: DataClayMetaData.

    :return: MetaData GRPC message.
    """
    if type(metadata) is common_messages.DataClayObjectMetaData:
        oids = dict()
        for k, v in metadata.oids.items():
            oids[k] = get_id(v)

        classids = dict()
        for k, v in metadata.classids.items():
            classids[k] = get_id(v)

        hints = dict()
        for k, v in metadata.hints.items():
            hints[k] = get_id(v)

        num_refs = metadata.numRefs
        orig_object_id = get_id(metadata.origObjectID)
        root_location = get_id(metadata.rootLocation)
        origin_location = get_id(metadata.originLocation)
        alias = metadata.alias
        dataset_name = metadata.dataset_name
        is_read_only = metadata.isReadOnly
        replica_locations = None
        if metadata.replicaLocations is not None:
            replica_locations = list()
            for replica_loc in metadata.replicaLocations:
                replica_locations.append(get_id(replica_loc))
        return DataClayObjectMetaData(
            alias,
            is_read_only,
            oids,
            classids,
            hints,
            num_refs,
            orig_object_id,
            root_location,
            origin_location,
            replica_locations,
            dataset_name,
        )

    else:

        one = dict()

        for k, v in metadata.tags_to_oids.items():
            one[k] = get_msg_id(v)

        two = dict()

        for k, v in metadata.tags_to_class_ids.items():
            two[k] = get_msg_id(v)

        three = dict()

        for k, v in metadata.tags_to_hints.items():
            three[k] = get_msg_id(v)

        replica_locs = None
        if metadata.replica_locations is not None:
            replica_locs = list()
            for replica_loc in metadata.replica_locations:
                replica_locs.append(get_msg_id(replica_loc))

        request = common_messages.DataClayObjectMetaData(
            oids=one,
            classids=two,
            hints=three,
            numRefs=metadata.num_refs_pointing_to_obj,
            origObjectID=get_msg_id(metadata.orig_object_id),
            rootLocation=get_msg_id(metadata.root_location),
            originLocation=get_msg_id(metadata.origin_location),
            replicaLocations=replica_locs,
            alias=metadata.alias,
            isReadOnly=metadata.is_read_only,
            dataset_name=metadata.dataset_name,
        )

        return request


def to_hex(val, nbits):
    """Convert a long to hex.

    :param val: long.

    :param nbits: The number of bit two's complement.

    :return: hex value.
    """
    return hex((val + (1 << nbits)) % (1 << nbits))


def convert_neg(x):
    """Convert negative hex not correctly converted.

    :param x: int.

    :return: Correct int.
    """
    if x > 9223372036854775808:
        x -= 18446744073709551616
    return x


def get_storage_location(storage_loc):
    if type(storage_loc) is common_messages.StorageLocationInfo:
        id = get_id(storage_loc.id)
        hostname = storage_loc.hostname
        name = storage_loc.name
        port = storage_loc.port
        return StorageLocation(id, hostname, name, port)
    else:
        response = common_messages.StorageLocationInfo(
            id=get_msg_id(storage_loc.object_id),
            hostname=storage_loc.hostname,
            name=storage_loc.name,
            port=storage_loc.port,
        )
        return response


def get_execution_environment(execution_environment):
    if type(execution_environment) is common_messages.ExecutionEnvironmentInfo:
        id = get_id(execution_environment.id)
        hostname = execution_environment.hostname
        dataclay_instance_id = get_id(execution_environment.dataClayInstanceID)
        name = execution_environment.sl_name
        port = execution_environment.port
        language = execution_environment.language
        return ExecutionEnvironment(id, hostname, name, port, language, dataclay_instance_id)
    else:
        response = common_messages.ExecutionEnvironmentInfo(
            id=get_msg_id(execution_environment.object_id),
            hostname=execution_environment.hostname,
            name=execution_environment.sl_name,
            port=execution_environment.port,
            language=execution_environment.language,
            dataClayInstanceID=get_msg_id(execution_environment.dataclay_instance_id),
        )
        return response


def get_dataclay_instance(dataclay_instance):
    if type(dataclay_instance) is common_messages.DataClayInstance:
        id = get_id(dataclay_instance.id)
        hosts = dataclay_instance.hosts
        ports = dataclay_instance.ports
        return DataClayInstance(id, hosts, ports)
    else:
        response = common_messages.DataClayInstance(
            id=get_msg_id(dataclay_instance.id),
            hosts=dataclay_instance.hosts,
            ports=dataclay_instance.ports,
        )
        return response


def get_metadata_info(metadata_info):
    if type(metadata_info) is common_messages.MetaDataInfo:

        if not hasattr(metadata_info, "id") or metadata_info.id == "" or metadata_info.id is None:
            return None

        id = get_id(metadata_info.id)
        is_read_only = metadata_info.is_read_only
        dataset_id = get_id(metadata_info.dataset_id)
        metaclass_id = get_id(metadata_info.metaclass_id)
        locations = set()
        for loc in metadata_info.locations:
            locations.append(get_id(loc))
        alias = metadata_info.alias
        owner_id = get_id(metadata_info.owner_id)

        return MetaDataInfo(id, is_read_only, dataset_id, metaclass_id, locations, alias, owner_id)
    else:
        locations_ids = set()
        for loc in metadata_info.locations:
            locations_ids.append(get_msg_id(loc))
        response = common_messages.MetaDataInfo(
            objectID=get_msg_id(metadata_info.id),
            isReadOnly=metadata_info.is_read_only,
            datasetID=get_msg_id(metadata_info.dataset_id),
            metaclassID=get_msg_id(metadata_info.metaclass_id),
            locations=locations_ids,
            alias=metadata_info.alias,
            ownerID=get_msg_id(metadata_info.owner_id),
        )
        return response


def get_obj_with_data_param_or_return(vol_param_or_ret):
    """
    :param vol_param_or_ret: Could be a protobuf msg or a tuple.

    :return: Could return a deserialized message or a ObjectWithDataParamOrReturn message.
    """
    if type(vol_param_or_ret) is common_messages.ObjectWithDataParamOrReturn:
        oid = get_id(vol_param_or_ret.oid)
        class_id = get_id(vol_param_or_ret.classid)
        mdata = get_metadata(vol_param_or_ret.metadata)
        byte_array = vol_param_or_ret.objbytes

        return ObjectWithDataParamOrReturn(oid, class_id, mdata, byte_array)
    else:
        response = common_messages.ObjectWithDataParamOrReturn(
            oid=get_msg_id(vol_param_or_ret.object_id),
            classid=get_msg_id(vol_param_or_ret.class_id),
            metadata=get_metadata(vol_param_or_ret.metadata),
            objbytes=vol_param_or_ret.obj_bytes,
        )
        return response


def get_lang_param_or_return(param_or_ret):
    """
    :param param_or_ret: Could be a protobuf msg or a list.

    :return: Could return a deserialized message or a LanguageParamOrReturn message.
    """
    if type(param_or_ret) is common_messages.LanguageParamOrReturn:
        mdata = get_metadata(param_or_ret.metadata)
        byte_array = param_or_ret.objbytes
        return mdata, byte_array

    else:
        request = common_messages.LanguageParamOrReturn(
            metadata=get_metadata(param_or_ret[0]), objbytes=param_or_ret[1]
        )

        return request


def get_immutable_param_or_return(param_or_ret):
    """
    :param param_or_ret: Could be a protobuf msg or a _io.BytesIO.

    :return: Could return a deserialized message or a ImmutableParamOrReturn message.
    """
    if type(param_or_ret) is common_messages.ImmutableParamOrReturn:
        byte_array = param_or_ret.objbytes
        return byte_array

    else:
        request = common_messages.ImmutableParamOrReturn(objbytes=param_or_ret)
        return request


def get_persistent_param_or_return(param_or_ret):
    """
    :param param_or_ret: Could be a PersistentParamOrReturn protobuf msg or a list.

    :return: Could return a deserialized message or a PersistentParamOrReturn message.
    """
    if type(param_or_ret) is common_messages.PersistentParamOrReturn:
        oid = get_id(param_or_ret.oid)
        class_id = get_id(param_or_ret.classID)
        hint = get_id(param_or_ret.hint)

        return PersistentParamOrReturn(oid, hint, class_id)

    else:
        class_id = param_or_ret.class_id
        oid = param_or_ret.object_id
        hint = param_or_ret.hint
        request = common_messages.PersistentParamOrReturn(
            oid=get_msg_id(oid), hint=get_msg_id(hint), classID=get_msg_id(class_id)
        )

        return request


def get_param_or_return(param_or_ret_msg):
    """
    :param param_or_ret_msg: Could be None, a SerializedParametersOrReturn protobuf msg or a list.

    :return: Could return an empty SerializedParametersOrReturn message, a deserialized message
             or a SerializedParametersOrReturn message.
    """
    if param_or_ret_msg is None:
        # create and return empty serialized message
        return common_messages.SerializedParametersOrReturn()
    elif type(param_or_ret_msg) is common_messages.SerializedParametersOrReturn:
        # create and return deserialized message
        num_params = param_or_ret_msg.numParams

        imm_objs = dict()
        lang_objs = dict()
        vol_objs = dict()
        pers_objs = dict()

        for k, v in param_or_ret_msg.immParams.items():
            imm_objs[k] = get_immutable_param_or_return(v)

        for k, v in param_or_ret_msg.langParams.items():
            lang_objs[k] = get_lang_param_or_return(v)

        for k, v in param_or_ret_msg.volatileParams.items():
            vol_objs[k] = get_obj_with_data_param_or_return(v)

        for k, v in param_or_ret_msg.persParams.items():
            pers_objs[k] = get_persistent_param_or_return(v)

        return SerializedParametersOrReturn(
            num_params=num_params,
            imm_objs=imm_objs,
            lang_objs=lang_objs,
            vol_objs=vol_objs,
            pers_objs=pers_objs,
        )
    elif type(param_or_ret_msg) is SerializedParametersOrReturn:
        # create and return serialized message
        imm_objs = dict()
        lang_objs = dict()
        vol_objs = dict()
        pers_objs = dict()
        num_params = param_or_ret_msg.num_params

        for k, v in param_or_ret_msg.imm_objs.items():
            imm_objs[k] = get_immutable_param_or_return(v)

        for k, v in param_or_ret_msg.lang_objs.items():
            lang_objs[k] = get_lang_param_or_return(v)

        for k, v in param_or_ret_msg.vol_objs.items():
            vol_objs[k] = get_obj_with_data_param_or_return(v)

        for k, v in param_or_ret_msg.persistent_refs.items():
            pers_objs[k] = get_persistent_param_or_return(v)

        request = common_messages.SerializedParametersOrReturn(
            numParams=num_params,
            immParams=imm_objs,
            langParams=lang_objs,
            volatileParams=vol_objs,
            persParams=pers_objs,
        )

        return request
    else:
        raise TypeError(
            "Param serialized_objs type is wrong. It could be None, SerializedParametersOrReturn protobuf msg or a list."
        )


def return_empty_message(resp_obs):
    """Return a protobuf empty message.

    :param resp_obs: string msg with UUID.
    """
    resp = common_messages.EmptyMessage()
    resp_obs(resp)


"""
HexByteConversion

Convert a byte string to it's hex representation for output or visa versa.

bye_to_hex converts byte string "\xFF\xFE\x00\x01" to the string "FF FE 00 01"
hex_to_byte converts string "FF FE 00 01" to the byte string "\xFF\xFE\x00\x01"
"""


def bye_to_hex(byte_str):
    """Convert a byte string to it's hex string representation e.g. for output.

    :param byte_str: byte string with UUID.
    :return: hex string msg with UUID.
    """

    # Uses list comprehension which is a fractionally faster implementation than
    # the alternative, more readable, implementation below
    #
    #    hex = []
    #    for aChar in byteStr:
    #        hex.append( "%02X " % ord( aChar ) )
    #
    #    return ''.join( hex ).strip()

    return "".join(["%02X " % ord(x) for x in byte_str]).strip()


def hex_to_byte(hex_str):
    """
    Convert a string hex byte values into a byte string. The Hex Byte values may
    or may not be space separated.
    :param hex_str: hex string msg with UUID.
    :return: byte string msg with UUID.
    """

    # The list comprehension implementation is fractionally slower in this case
    #
    #    hexStr = ''.join( hexStr.split(" ") )
    #    return ''.join( ["%c" % chr( int ( hexStr[i:i+2],16 ) ) \
    #                                   for i in range(0, len( hexStr ), 2) ] )

    bytes_str = []

    hex_str = "".join(hex_str.split(" "))

    for i in range(0, len(hex_str), 2):
        bytes_str.append(chr(int(hex_str[i : i + 2], 16)))

    return "".join(bytes_str)


def prepare_exception(message, stack):
    """
    Prepare message + stack for proto messages
    :param message: message of the exception.
    :param stack: stackTrace of the exception.
    :return: final string
    """
    if message is not None:
        return prepare_bytes(
            "\n"
            + "-" * 146
            + "\nError Message: "
            + message
            + "\n"
            + "-" * 146
            + "\nServer "
            + str(stack)
            + "\n"
            + "-" * 146
        )
    else:
        return prepare_bytes(
            "\n"
            + "-" * 146
            + "\nError Stack: \n"
            + "-" * 146
            + "\nServer "
            + str(stack)
            + "\n"
            + "-" * 146
        )


def return_stack():
    """
    Create the stack of the obtained exception
    :return: string stacktrace.
    """
    exc_type, exc_value, exc_traceback = sys.exc_info()
    lines = traceback.format_exception(exc_type, exc_value, exc_traceback)

    return lines[0] + lines[1]


def prepare_bytes(varz):
    """Create the right bytes var for python2/3.
    :param varx: variable to convert in bytes.
    :return: correct bytes of varz.
    """
    if six.PY2:
        v = bytes(varz)
    elif six.PY3:
        v = bytes(varz, "utf-8")
    return v
