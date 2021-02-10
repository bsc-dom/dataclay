
""" Class description goes here. """
from dataclay.serialization.lib.SerializedParametersOrReturn import SerializedParametersOrReturn

"""Utility methods for gRPC clients/server."""

import logging
import sys
import traceback
import uuid
import six

import dataclay.communication.grpc.messages.common.common_messages_pb2 as common_messages

__author__ = 'Enrico La Sala <enrico.lasala@bsc.es>'
__copyright__ = '2017 Barcelona Supercomputing Center (BSC-CNS)'

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
    return str(id)

def get_id(id_msg):
    """Create the ID based on protobuf message.

    :param id_msg: Common protobuf message with uuid_most and uuid_least.

    :return: UUID based on param.
    """    
    if id_msg is None:
        return None
    elif id_msg.uuid == "":
        return None
    else:
        return uuid.UUID(id_msg.uuid)


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
        
        return oids, classids, hints, num_refs

    else:

        one = dict()
    
        for k, v in metadata[0].items():
            one[k] = get_msg_id(v)
    
        two = dict()
    
        for k, v in metadata[1].items():
            two[k] = get_msg_id(v)

        three = dict()

        for k, v in metadata[2].items():
            three[k] = get_msg_id(v)

        request = common_messages.DataClayObjectMetaData(
            oids=one,
            classids=two,
            hints=three,
            numRefs=metadata[3]
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

        return oid, class_id, mdata, byte_array
    else:
        response = common_messages.ObjectWithDataParamOrReturn(
            oid=get_msg_id(vol_param_or_ret[0]),
            classid=get_msg_id(vol_param_or_ret[1]),
            metadata=get_metadata(vol_param_or_ret[2]),
            objbytes=vol_param_or_ret[3]
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
            metadata=get_metadata(param_or_ret[0]),
            objbytes=param_or_ret[1]
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
        request = common_messages.ImmutableParamOrReturn(
            objbytes=param_or_ret
        )
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

        return oid, hint, class_id

    else:
        class_id = None
        hint = None
        oid = param_or_ret[0]

        if param_or_ret[1] is not None:
            hint = param_or_ret[1]

        if param_or_ret[2] is not None:
            class_id = param_or_ret[2]

        request = common_messages.PersistentParamOrReturn(
            oid=get_msg_id(oid),
            hint=get_msg_id(hint),
            classID=get_msg_id(class_id))

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
            
        return SerializedParametersOrReturn(num_params, imm_objs, lang_objs, vol_objs, pers_objs)
    elif type(param_or_ret_msg) is SerializedParametersOrReturn:
        # create and return serialized message
        num_params = param_or_ret_msg.num_params
        imm_objs = param_or_ret_msg.imm_objs
        lang_objs = param_or_ret_msg.lang_objs
        vol_objs = param_or_ret_msg.vol_objs
        pers_obj = param_or_ret_msg.persistent_refs
        
        for k, v in param_or_ret_msg[1].items():
            imm_objs[k] = get_immutable_param_or_return(v)
        
        for k, v in param_or_ret_msg[2].items():
            lang_objs[k] = get_lang_param_or_return(v)
        
        for k, v in param_or_ret_msg[3].items():
            vol_objs[k] = get_obj_with_data_param_or_return(v)
        
        for k, v in param_or_ret_msg[4].items():
            pers_obj[k] = get_persistent_param_or_return(v)

        request = common_messages.SerializedParametersOrReturn(
                numParams=num_params,
                immParams=imm_objs,
                langParams=lang_objs,
                volatileParams=vol_objs,
                persParams=pers_obj
        )
        
        return request
    else:
        raise TypeError("Param serialized_objs type is wrong. It could be None, SerializedParametersOrReturn protobuf msg or a list.")


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

    return ''.join(["%02X " % ord(x) for x in byte_str]).strip()


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

    hex_str = ''.join(hex_str.split(" "))

    for i in range(0, len(hex_str), 2):
        bytes_str.append(chr(int(hex_str[i:i + 2], 16)))

    return ''.join(bytes_str)


def prepare_exception(message, stack):
    """
    Prepare message + stack for proto messages
    :param message: message of the exception.
    :param stack: stackTrace of the exception.
    :return: final string
    """
    if message is not None:
        return prepare_bytes("\n" + "-"*146 + "\nError Message: " + message + "\n" + "-"*146 + "\nServer " + str(stack) + "\n" + "-"*146)
    else:
        return prepare_bytes("\n" + "-"*146 + "\nError Stack: \n" + "-"*146 + "\nServer " + str(stack) + "\n" + "-"*146)


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