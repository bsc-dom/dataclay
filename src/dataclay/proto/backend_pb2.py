# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: proto/backend.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from google.protobuf import wrappers_pb2 as google_dot_protobuf_dot_wrappers__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x13proto/backend.proto\x12\rproto.backend\x1a\x1bgoogle/protobuf/empty.proto\x1a\x1egoogle/protobuf/wrappers.proto\",\n\x15MakePersistentRequest\x12\x13\n\x0bpickled_obj\x18\x01 \x03(\x0c\"s\n\x17\x43\x61llActiveMethodRequest\x12\x12\n\nsession_id\x18\x01 \x01(\t\x12\x11\n\tobject_id\x18\x02 \x01(\t\x12\x13\n\x0bmethod_name\x18\x03 \x01(\t\x12\x0c\n\x04\x61rgs\x18\x04 \x01(\x0c\x12\x0e\n\x06kwargs\x18\x05 \x01(\x0c\"?\n\x18\x43\x61llActiveMethodResponse\x12\r\n\x05value\x18\x01 \x01(\x0c\x12\x14\n\x0cis_exception\x18\x02 \x01(\x08\"/\n\x1aGetObjectPropertiesRequest\x12\x11\n\tobject_id\x18\x01 \x01(\t\"Q\n\x1dUpdateObjectPropertiesRequest\x12\x11\n\tobject_id\x18\x01 \x01(\t\x12\x1d\n\x15serialized_properties\x18\x02 \x01(\x0c\"M\n\x11MoveObjectRequest\x12\x11\n\tobject_id\x18\x01 \x01(\t\x12\x12\n\nbackend_id\x18\x02 \x01(\t\x12\x11\n\trecursive\x18\x03 \x01(\x08\"Y\n\x11SendObjectRequest\x12\x12\n\nsession_id\x18\x01 \x01(\t\x12\x11\n\tobject_id\x18\x02 \x01(\t\x12\x1d\n\x15serialized_properties\x18\x03 \x01(\x0c\",\n\x17NewObjectVersionRequest\x12\x11\n\tobject_id\x18\x01 \x01(\t\"4\n\x1f\x43onsolidateObjectVersionRequest\x12\x11\n\tobject_id\x18\x01 \x01(\t\"2\n\x18NewObjectVersionResponse\x12\x16\n\x0eobject_full_id\x18\x01 \x01(\t\"@\n\x14ProxifyObjectRequest\x12\x11\n\tobject_id\x18\x01 \x01(\t\x12\x15\n\rnew_object_id\x18\x02 \x01(\t\"A\n\x15\x43hangeObjectIdRequest\x12\x11\n\tobject_id\x18\x01 \x01(\t\x12\x15\n\rnew_object_id\x18\x02 \x01(\t2\xc6\x08\n\x0e\x42\x61\x63kendService\x12P\n\x0eMakePersistent\x12$.proto.backend.MakePersistentRequest\x1a\x16.google.protobuf.Empty\"\x00\x12\x65\n\x10\x43\x61llActiveMethod\x12&.proto.backend.CallActiveMethodRequest\x1a\'.proto.backend.CallActiveMethodResponse\"\x00\x12_\n\x13GetObjectProperties\x12).proto.backend.GetObjectPropertiesRequest\x1a\x1b.google.protobuf.BytesValue\"\x00\x12`\n\x16UpdateObjectProperties\x12,.proto.backend.UpdateObjectPropertiesRequest\x1a\x16.google.protobuf.Empty\"\x00\x12H\n\nMoveObject\x12 .proto.backend.MoveObjectRequest\x1a\x16.google.protobuf.Empty\"\x00\x12H\n\nSendObject\x12 .proto.backend.SendObjectRequest\x1a\x16.google.protobuf.Empty\"\x00\x12\x65\n\x10NewObjectVersion\x12&.proto.backend.NewObjectVersionRequest\x1a\'.proto.backend.NewObjectVersionResponse\"\x00\x12\x64\n\x18\x43onsolidateObjectVersion\x12..proto.backend.ConsolidateObjectVersionRequest\x1a\x16.google.protobuf.Empty\"\x00\x12N\n\rProxifyObject\x12#.proto.backend.ProxifyObjectRequest\x1a\x16.google.protobuf.Empty\"\x00\x12P\n\x0e\x43hangeObjectId\x12$.proto.backend.ChangeObjectIdRequest\x1a\x16.google.protobuf.Empty\"\x00\x12<\n\x08\x46lushAll\x12\x16.google.protobuf.Empty\x1a\x16.google.protobuf.Empty\"\x00\x12<\n\x08Shutdown\x12\x16.google.protobuf.Empty\x1a\x16.google.protobuf.Empty\"\x00\x12\x39\n\x05\x44rain\x12\x16.google.protobuf.Empty\x1a\x16.google.protobuf.Empty\"\x00\x62\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'proto.backend_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _MAKEPERSISTENTREQUEST._serialized_start=99
  _MAKEPERSISTENTREQUEST._serialized_end=143
  _CALLACTIVEMETHODREQUEST._serialized_start=145
  _CALLACTIVEMETHODREQUEST._serialized_end=260
  _CALLACTIVEMETHODRESPONSE._serialized_start=262
  _CALLACTIVEMETHODRESPONSE._serialized_end=325
  _GETOBJECTPROPERTIESREQUEST._serialized_start=327
  _GETOBJECTPROPERTIESREQUEST._serialized_end=374
  _UPDATEOBJECTPROPERTIESREQUEST._serialized_start=376
  _UPDATEOBJECTPROPERTIESREQUEST._serialized_end=457
  _MOVEOBJECTREQUEST._serialized_start=459
  _MOVEOBJECTREQUEST._serialized_end=536
  _SENDOBJECTREQUEST._serialized_start=538
  _SENDOBJECTREQUEST._serialized_end=627
  _NEWOBJECTVERSIONREQUEST._serialized_start=629
  _NEWOBJECTVERSIONREQUEST._serialized_end=673
  _CONSOLIDATEOBJECTVERSIONREQUEST._serialized_start=675
  _CONSOLIDATEOBJECTVERSIONREQUEST._serialized_end=727
  _NEWOBJECTVERSIONRESPONSE._serialized_start=729
  _NEWOBJECTVERSIONRESPONSE._serialized_end=779
  _PROXIFYOBJECTREQUEST._serialized_start=781
  _PROXIFYOBJECTREQUEST._serialized_end=845
  _CHANGEOBJECTIDREQUEST._serialized_start=847
  _CHANGEOBJECTIDREQUEST._serialized_end=912
  _BACKENDSERVICE._serialized_start=915
  _BACKENDSERVICE._serialized_end=2009
# @@protoc_insertion_point(module_scope)