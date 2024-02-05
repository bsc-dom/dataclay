# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: dataclay/proto/backend/backend.proto
# Protobuf Python Version: 4.25.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from google.protobuf import wrappers_pb2 as google_dot_protobuf_dot_wrappers__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n$dataclay/proto/backend/backend.proto\x12\x16\x64\x61taclay.proto.backend\x1a\x1bgoogle/protobuf/empty.proto\x1a\x1egoogle/protobuf/wrappers.proto\",\n\x15MakePersistentRequest\x12\x13\n\x0bpickled_obj\x18\x01 \x03(\x0c\"s\n\x17\x43\x61llActiveMethodRequest\x12\x12\n\nsession_id\x18\x01 \x01(\t\x12\x11\n\tobject_id\x18\x02 \x01(\t\x12\x13\n\x0bmethod_name\x18\x03 \x01(\t\x12\x0c\n\x04\x61rgs\x18\x04 \x01(\x0c\x12\x0e\n\x06kwargs\x18\x05 \x01(\x0c\"?\n\x18\x43\x61llActiveMethodResponse\x12\r\n\x05value\x18\x01 \x01(\x0c\x12\x14\n\x0cis_exception\x18\x02 \x01(\x08\"A\n\x19GetObjectAttributeRequest\x12\x11\n\tobject_id\x18\x01 \x01(\t\x12\x11\n\tattribute\x18\x02 \x01(\t\"_\n\x19SetObjectAttributeRequest\x12\x11\n\tobject_id\x18\x01 \x01(\t\x12\x11\n\tattribute\x18\x02 \x01(\t\x12\x1c\n\x14serialized_attribute\x18\x03 \x01(\x0c\"A\n\x19\x44\x65lObjectAttributeRequest\x12\x11\n\tobject_id\x18\x01 \x01(\t\x12\x11\n\tattribute\x18\x02 \x01(\t\"/\n\x1aGetObjectPropertiesRequest\x12\x11\n\tobject_id\x18\x01 \x01(\t\"Q\n\x1dUpdateObjectPropertiesRequest\x12\x11\n\tobject_id\x18\x01 \x01(\t\x12\x1d\n\x15serialized_properties\x18\x02 \x01(\x0c\"v\n\x12SendObjectsRequest\x12\x12\n\nobject_ids\x18\x01 \x03(\t\x12\x12\n\nbackend_id\x18\x02 \x01(\t\x12\x14\n\x0cmake_replica\x18\x03 \x01(\x08\x12\x11\n\trecursive\x18\x04 \x01(\x08\x12\x0f\n\x07remotes\x18\x05 \x01(\x08\"B\n\x16RegisterObjectsRequest\x12\x12\n\ndict_bytes\x18\x01 \x03(\x0c\x12\x14\n\x0cmake_replica\x18\x02 \x01(\x08\",\n\x17NewObjectVersionRequest\x12\x11\n\tobject_id\x18\x01 \x01(\t\"/\n\x18NewObjectVersionResponse\x12\x13\n\x0bobject_info\x18\x01 \x01(\t\"4\n\x1f\x43onsolidateObjectVersionRequest\x12\x11\n\tobject_id\x18\x01 \x01(\t\"@\n\x14ProxifyObjectRequest\x12\x11\n\tobject_id\x18\x01 \x01(\t\x12\x15\n\rnew_object_id\x18\x02 \x01(\t\"A\n\x15\x43hangeObjectIdRequest\x12\x11\n\tobject_id\x18\x01 \x01(\t\x12\x15\n\rnew_object_id\x18\x02 \x01(\t\"d\n\x17NewObjectReplicaRequest\x12\x11\n\tobject_id\x18\x01 \x01(\t\x12\x12\n\nbackend_id\x18\x02 \x01(\t\x12\x11\n\trecursive\x18\x03 \x01(\x08\x12\x0f\n\x07remotes\x18\x04 \x01(\x08\x32\xc7\x0c\n\x0e\x42\x61\x63kendService\x12Y\n\x0eMakePersistent\x12-.dataclay.proto.backend.MakePersistentRequest\x1a\x16.google.protobuf.Empty\"\x00\x12w\n\x10\x43\x61llActiveMethod\x12/.dataclay.proto.backend.CallActiveMethodRequest\x1a\x30.dataclay.proto.backend.CallActiveMethodResponse\"\x00\x12\x66\n\x12GetObjectAttribute\x12\x31.dataclay.proto.backend.GetObjectAttributeRequest\x1a\x1b.google.protobuf.BytesValue\"\x00\x12\x61\n\x12SetObjectAttribute\x12\x31.dataclay.proto.backend.SetObjectAttributeRequest\x1a\x16.google.protobuf.Empty\"\x00\x12\x61\n\x12\x44\x65lObjectAttribute\x12\x31.dataclay.proto.backend.DelObjectAttributeRequest\x1a\x16.google.protobuf.Empty\"\x00\x12h\n\x13GetObjectProperties\x12\x32.dataclay.proto.backend.GetObjectPropertiesRequest\x1a\x1b.google.protobuf.BytesValue\"\x00\x12i\n\x16UpdateObjectProperties\x12\x35.dataclay.proto.backend.UpdateObjectPropertiesRequest\x1a\x16.google.protobuf.Empty\"\x00\x12S\n\x0bSendObjects\x12*.dataclay.proto.backend.SendObjectsRequest\x1a\x16.google.protobuf.Empty\"\x00\x12[\n\x0fRegisterObjects\x12..dataclay.proto.backend.RegisterObjectsRequest\x1a\x16.google.protobuf.Empty\"\x00\x12w\n\x10NewObjectVersion\x12/.dataclay.proto.backend.NewObjectVersionRequest\x1a\x30.dataclay.proto.backend.NewObjectVersionResponse\"\x00\x12m\n\x18\x43onsolidateObjectVersion\x12\x37.dataclay.proto.backend.ConsolidateObjectVersionRequest\x1a\x16.google.protobuf.Empty\"\x00\x12W\n\rProxifyObject\x12,.dataclay.proto.backend.ProxifyObjectRequest\x1a\x16.google.protobuf.Empty\"\x00\x12Y\n\x0e\x43hangeObjectId\x12-.dataclay.proto.backend.ChangeObjectIdRequest\x1a\x16.google.protobuf.Empty\"\x00\x12]\n\x10NewObjectReplica\x12/.dataclay.proto.backend.NewObjectReplicaRequest\x1a\x16.google.protobuf.Empty\"\x00\x12<\n\x08\x46lushAll\x12\x16.google.protobuf.Empty\x1a\x16.google.protobuf.Empty\"\x00\x12\x38\n\x04Stop\x12\x16.google.protobuf.Empty\x1a\x16.google.protobuf.Empty\"\x00\x12\x39\n\x05\x44rain\x12\x16.google.protobuf.Empty\x1a\x16.google.protobuf.Empty\"\x00\x42!\n\x1d\x65s.bsc.dataclay.proto.backendP\x01\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'dataclay.proto.backend.backend_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  _globals['DESCRIPTOR']._options = None
  _globals['DESCRIPTOR']._serialized_options = b'\n\035es.bsc.dataclay.proto.backendP\001'
  _globals['_MAKEPERSISTENTREQUEST']._serialized_start=125
  _globals['_MAKEPERSISTENTREQUEST']._serialized_end=169
  _globals['_CALLACTIVEMETHODREQUEST']._serialized_start=171
  _globals['_CALLACTIVEMETHODREQUEST']._serialized_end=286
  _globals['_CALLACTIVEMETHODRESPONSE']._serialized_start=288
  _globals['_CALLACTIVEMETHODRESPONSE']._serialized_end=351
  _globals['_GETOBJECTATTRIBUTEREQUEST']._serialized_start=353
  _globals['_GETOBJECTATTRIBUTEREQUEST']._serialized_end=418
  _globals['_SETOBJECTATTRIBUTEREQUEST']._serialized_start=420
  _globals['_SETOBJECTATTRIBUTEREQUEST']._serialized_end=515
  _globals['_DELOBJECTATTRIBUTEREQUEST']._serialized_start=517
  _globals['_DELOBJECTATTRIBUTEREQUEST']._serialized_end=582
  _globals['_GETOBJECTPROPERTIESREQUEST']._serialized_start=584
  _globals['_GETOBJECTPROPERTIESREQUEST']._serialized_end=631
  _globals['_UPDATEOBJECTPROPERTIESREQUEST']._serialized_start=633
  _globals['_UPDATEOBJECTPROPERTIESREQUEST']._serialized_end=714
  _globals['_SENDOBJECTSREQUEST']._serialized_start=716
  _globals['_SENDOBJECTSREQUEST']._serialized_end=834
  _globals['_REGISTEROBJECTSREQUEST']._serialized_start=836
  _globals['_REGISTEROBJECTSREQUEST']._serialized_end=902
  _globals['_NEWOBJECTVERSIONREQUEST']._serialized_start=904
  _globals['_NEWOBJECTVERSIONREQUEST']._serialized_end=948
  _globals['_NEWOBJECTVERSIONRESPONSE']._serialized_start=950
  _globals['_NEWOBJECTVERSIONRESPONSE']._serialized_end=997
  _globals['_CONSOLIDATEOBJECTVERSIONREQUEST']._serialized_start=999
  _globals['_CONSOLIDATEOBJECTVERSIONREQUEST']._serialized_end=1051
  _globals['_PROXIFYOBJECTREQUEST']._serialized_start=1053
  _globals['_PROXIFYOBJECTREQUEST']._serialized_end=1117
  _globals['_CHANGEOBJECTIDREQUEST']._serialized_start=1119
  _globals['_CHANGEOBJECTIDREQUEST']._serialized_end=1184
  _globals['_NEWOBJECTREPLICAREQUEST']._serialized_start=1186
  _globals['_NEWOBJECTREPLICAREQUEST']._serialized_end=1286
  _globals['_BACKENDSERVICE']._serialized_start=1289
  _globals['_BACKENDSERVICE']._serialized_end=2896
# @@protoc_insertion_point(module_scope)
