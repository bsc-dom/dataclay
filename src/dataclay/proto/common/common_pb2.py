# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: dataclay/proto/common/common.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\"dataclay/proto/common/common.proto\x12\x15\x64\x61taclay.proto.common\"F\n\x07\x42\x61\x63kend\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0c\n\x04host\x18\x02 \x01(\t\x12\x0c\n\x04port\x18\x03 \x01(\x05\x12\x13\n\x0b\x64\x61taclay_id\x18\x04 \x01(\t\"\xcd\x01\n\x0eObjectMetadata\x12\n\n\x02id\x18\x01 \x01(\t\x12\x14\n\x0c\x64\x61taset_name\x18\x02 \x01(\t\x12\x12\n\nclass_name\x18\x03 \x01(\t\x12\x19\n\x11master_backend_id\x18\x04 \x01(\t\x12\x1b\n\x13replica_backend_ids\x18\x05 \x03(\t\x12\x14\n\x0cis_read_only\x18\x06 \x01(\x08\x12\x1a\n\x12original_object_id\x18\x07 \x01(\t\x12\x1b\n\x13versions_object_ids\x18\x08 \x03(\t\"P\n\x07Session\x12\n\n\x02id\x18\x01 \x01(\t\x12\x10\n\x08username\x18\x02 \x01(\t\x12\x14\n\x0c\x64\x61taset_name\x18\x03 \x01(\t\x12\x11\n\tis_active\x18\x04 \x01(\x08\"C\n\x08\x44\x61taclay\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0c\n\x04host\x18\x02 \x01(\t\x12\x0c\n\x04port\x18\x03 \x01(\x05\x12\x0f\n\x07is_this\x18\x04 \x01(\x08\">\n\x05\x41lias\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x14\n\x0c\x64\x61taset_name\x18\x02 \x01(\t\x12\x11\n\tobject_id\x18\x03 \x01(\tB \n\x1c\x65s.bsc.dataclay.proto.commonP\x01\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'dataclay.proto.common.common_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'\n\034es.bsc.dataclay.proto.commonP\001'
  _globals['_BACKEND']._serialized_start=61
  _globals['_BACKEND']._serialized_end=131
  _globals['_OBJECTMETADATA']._serialized_start=134
  _globals['_OBJECTMETADATA']._serialized_end=339
  _globals['_SESSION']._serialized_start=341
  _globals['_SESSION']._serialized_end=421
  _globals['_DATACLAY']._serialized_start=423
  _globals['_DATACLAY']._serialized_end=490
  _globals['_ALIAS']._serialized_start=492
  _globals['_ALIAS']._serialized_end=554
# @@protoc_insertion_point(module_scope)
