# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: protos/dataservice.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from google.protobuf import wrappers_pb2 as google_dot_protobuf_dot_wrappers__pb2
from . import dataservice_messages_pb2 as protos_dot_dataservice__messages__pb2
from . import common_messages_pb2 as protos_dot_common__messages__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x18protos/dataservice.proto\x12\x12protos.dataservice\x1a\x1bgoogle/protobuf/empty.proto\x1a\x1egoogle/protobuf/wrappers.proto\x1a!protos/dataservice_messages.proto\x1a\x1cprotos/common_messages.proto\"@\n\x15MakePersistentRequest\x12\x12\n\nsession_id\x18\x01 \x01(\t\x12\x13\n\x0bpickled_obj\x18\x02 \x03(\x0c\"s\n\x17\x43\x61llActiveMethodRequest\x12\x12\n\nsession_id\x18\x01 \x01(\t\x12\x11\n\tobject_id\x18\x02 \x01(\t\x12\x13\n\x0bmethod_name\x18\x03 \x01(\t\x12\x0c\n\x04\x61rgs\x18\x04 \x01(\x0c\x12\x0e\n\x06kwargs\x18\x05 \x01(\x0c\"R\n\x16GetCopyOfObjectRequest\x12\x12\n\nsession_id\x18\x01 \x01(\t\x12\x11\n\tobject_id\x18\x02 \x01(\t\x12\x11\n\trecursive\x18\x03 \x01(\x08\"[\n\x13UpdateObjectRequest\x12\x12\n\nsession_id\x18\x01 \x01(\t\x12\x11\n\tobject_id\x18\x02 \x01(\t\x12\x1d\n\x15serialized_properties\x18\x03 \x01(\x0c\"a\n\x11MoveObjectRequest\x12\x12\n\nsession_id\x18\x01 \x01(\t\x12\x11\n\tobject_id\x18\x02 \x01(\t\x12\x12\n\nbackend_id\x18\x03 \x01(\t\x12\x11\n\trecursive\x18\x04 \x01(\x08\"Y\n\x11SendObjectRequest\x12\x12\n\nsession_id\x18\x01 \x01(\t\x12\x11\n\tobject_id\x18\x02 \x01(\t\x12\x1d\n\x15serialized_properties\x18\x03 \x01(\x0c\x32\xbf%\n\x0b\x44\x61taService\x12Y\n\rinitBackendID\x12(.protos.dataservice.InitBackendIDRequest\x1a\x1c.protos.common.ExceptionInfo\"\x00\x12y\n\x1d\x61ssociateExecutionEnvironment\x12\x38.protos.dataservice.AssociateExecutionEnvironmentRequest\x1a\x1c.protos.common.ExceptionInfo\"\x00\x12\x61\n\x11\x64\x65ployMetaClasses\x12,.protos.dataservice.DeployMetaClassesRequest\x1a\x1c.protos.common.ExceptionInfo\"\x00\x12Y\n\rdeployClasses\x12(.protos.dataservice.DeployClassesRequest\x1a\x1c.protos.common.ExceptionInfo\"\x00\x12U\n\x0b\x65nrichClass\x12&.protos.dataservice.EnrichClassRequest\x1a\x1c.protos.common.ExceptionInfo\"\x00\x12~\n\x15newPersistentInstance\x12\x30.protos.dataservice.NewPersistentInstanceRequest\x1a\x31.protos.dataservice.NewPersistentInstanceResponse\"\x00\x12W\n\x0cstoreObjects\x12\'.protos.dataservice.StoreObjectsRequest\x1a\x1c.protos.common.ExceptionInfo\"\x00\x12]\n\ngetObjects\x12%.protos.dataservice.GetObjectsRequest\x1a&.protos.dataservice.GetObjectsResponse\"\x00\x12]\n\nnewVersion\x12%.protos.dataservice.NewVersionRequest\x1a&.protos.dataservice.NewVersionResponse\"\x00\x12\x63\n\x12\x63onsolidateVersion\x12-.protos.dataservice.ConsolidateVersionRequest\x1a\x1c.protos.common.ExceptionInfo\"\x00\x12Y\n\rupsertObjects\x12(.protos.dataservice.UpsertObjectsRequest\x1a\x1c.protos.common.ExceptionInfo\"\x00\x12]\n\nnewReplica\x12%.protos.dataservice.NewReplicaRequest\x1a&.protos.dataservice.NewReplicaResponse\"\x00\x12\x66\n\rremoveObjects\x12(.protos.dataservice.RemoveObjectsRequest\x1a).protos.dataservice.RemoveObjectsResponse\"\x00\x12s\n\x18migrateObjectsToBackends\x12).protos.dataservice.MigrateObjectsRequest\x1a*.protos.dataservice.MigrateObjectsResponse\"\x00\x12\x93\x01\n\x1cgetClassIDFromObjectInMemory\x12\x37.protos.dataservice.GetClassIDFromObjectInMemoryRequest\x1a\x38.protos.dataservice.GetClassIDFromObjectInMemoryResponse\"\x00\x12~\n\x15\x65xecuteImplementation\x12\x30.protos.dataservice.ExecuteImplementationRequest\x1a\x31.protos.dataservice.ExecuteImplementationResponse\"\x00\x12^\n\x0emakePersistent\x12,.protos.dataservice.OldMakePersistentRequest\x1a\x1c.protos.common.ExceptionInfo\"\x00\x12O\n\x08\x66\x65\x64\x65rate\x12#.protos.dataservice.FederateRequest\x1a\x1c.protos.common.ExceptionInfo\"\x00\x12S\n\nunfederate\x12%.protos.dataservice.UnfederateRequest\x1a\x1c.protos.common.ExceptionInfo\"\x00\x12_\n\x10notifyFederation\x12+.protos.dataservice.NotifyFederationRequest\x1a\x1c.protos.common.ExceptionInfo\"\x00\x12\x63\n\x12notifyUnfederation\x12-.protos.dataservice.NotifyUnfederationRequest\x1a\x1c.protos.common.ExceptionInfo\"\x00\x12Q\n\x06\x65xists\x12!.protos.dataservice.ExistsRequest\x1a\".protos.dataservice.ExistsResponse\"\x00\x12U\n\x0bsynchronize\x12&.protos.dataservice.SynchronizeRequest\x1a\x1c.protos.common.ExceptionInfo\"\x00\x12Q\n\tstoreToDB\x12$.protos.dataservice.StoreToDBRequest\x1a\x1c.protos.common.ExceptionInfo\"\x00\x12Z\n\tgetFromDB\x12$.protos.dataservice.GetFromDBRequest\x1a%.protos.dataservice.GetFromDBResponse\"\x00\x12S\n\nupdateToDB\x12%.protos.dataservice.UpdateToDBRequest\x1a\x1c.protos.common.ExceptionInfo\"\x00\x12S\n\ndeleteToDB\x12%.protos.dataservice.DeleteToDBRequest\x1a\x1c.protos.common.ExceptionInfo\"\x00\x12]\n\x0f\x64\x65leteSetFromDB\x12*.protos.dataservice.DeleteSetFromDBRequest\x1a\x1c.protos.common.ExceptionInfo\"\x00\x12]\n\nexistsInDB\x12%.protos.dataservice.ExistsInDBRequest\x1a&.protos.dataservice.ExistsInDBResponse\"\x00\x12[\n\x1c\x63leanExecutionClassDirectory\x12\x1b.protos.common.EmptyMessage\x1a\x1c.protos.common.ExceptionInfo\"\x00\x12M\n\x0e\x63loseDbHandler\x12\x1b.protos.common.EmptyMessage\x1a\x1c.protos.common.ExceptionInfo\"\x00\x12G\n\x08shutDown\x12\x1b.protos.common.EmptyMessage\x1a\x1c.protos.common.ExceptionInfo\"\x00\x12S\n\x14\x64isconnectFromOthers\x12\x1b.protos.common.EmptyMessage\x1a\x1c.protos.common.ExceptionInfo\"\x00\x12U\n\x16registerPendingObjects\x12\x1b.protos.common.EmptyMessage\x1a\x1c.protos.common.ExceptionInfo\"\x00\x12J\n\x0b\x63leanCaches\x12\x1b.protos.common.EmptyMessage\x1a\x1c.protos.common.ExceptionInfo\"\x00\x12]\n\x0f\x61\x63tivateTracing\x12*.protos.dataservice.ActivateTracingRequest\x1a\x1c.protos.common.ExceptionInfo\"\x00\x12P\n\x11\x64\x65\x61\x63tivateTracing\x12\x1b.protos.common.EmptyMessage\x1a\x1c.protos.common.ExceptionInfo\"\x00\x12L\n\tgetTraces\x12\x1b.protos.common.EmptyMessage\x1a .protos.common.GetTracesResponse\"\x00\x12U\n\x0b\x64\x65leteAlias\x12&.protos.dataservice.DeleteAliasRequest\x1a\x1c.protos.common.ExceptionInfo\"\x00\x12m\n\x17\x64\x65tachObjectFromSession\x12\x32.protos.dataservice.DetachObjectFromSessionRequest\x1a\x1c.protos.common.ExceptionInfo\"\x00\x12_\n\x10\x63loseSessionInDS\x12+.protos.dataservice.CloseSessionInDSRequest\x1a\x1c.protos.common.ExceptionInfo\"\x00\x12i\n\x15getRetainedReferences\x12\x1b.protos.common.EmptyMessage\x1a\x31.protos.dataservice.GetRetainedReferencesResponse\"\x00\x12T\n\rgetNumObjects\x12\x1b.protos.common.EmptyMessage\x1a$.protos.common.GetNumObjectsResponse\"\x00\x12X\n\x11getNumObjectsInEE\x12\x1b.protos.common.EmptyMessage\x1a$.protos.common.GetNumObjectsResponse\"\x00\x12[\n\x0egetObjectGraph\x12\x1b.protos.common.EmptyMessage\x1a*.protos.dataservice.GetObjectGraphResponse\"\x00\x12U\n\x0eMakePersistent\x12).protos.dataservice.MakePersistentRequest\x1a\x16.google.protobuf.Empty\"\x00\x12^\n\x10\x43\x61llActiveMethod\x12+.protos.dataservice.CallActiveMethodRequest\x1a\x1b.google.protobuf.BytesValue\"\x00\x12\\\n\x0fGetCopyOfObject\x12*.protos.dataservice.GetCopyOfObjectRequest\x1a\x1b.google.protobuf.BytesValue\"\x00\x12Q\n\x0cUpdateObject\x12\'.protos.dataservice.UpdateObjectRequest\x1a\x16.google.protobuf.Empty\"\x00\x12M\n\nMoveObject\x12%.protos.dataservice.MoveObjectRequest\x1a\x16.google.protobuf.Empty\"\x00\x12M\n\nSendObject\x12%.protos.dataservice.SendObjectRequest\x1a\x16.google.protobuf.Empty\"\x00\x42R\n8es.bsc.dataclay.communication.grpc.generated.dataserviceB\x16\x44\x61taServiceGrpcServiceb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'protos.dataservice_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'\n8es.bsc.dataclay.communication.grpc.generated.dataserviceB\026DataServiceGrpcService'
  _MAKEPERSISTENTREQUEST._serialized_start=174
  _MAKEPERSISTENTREQUEST._serialized_end=238
  _CALLACTIVEMETHODREQUEST._serialized_start=240
  _CALLACTIVEMETHODREQUEST._serialized_end=355
  _GETCOPYOFOBJECTREQUEST._serialized_start=357
  _GETCOPYOFOBJECTREQUEST._serialized_end=439
  _UPDATEOBJECTREQUEST._serialized_start=441
  _UPDATEOBJECTREQUEST._serialized_end=532
  _MOVEOBJECTREQUEST._serialized_start=534
  _MOVEOBJECTREQUEST._serialized_end=631
  _SENDOBJECTREQUEST._serialized_start=633
  _SENDOBJECTREQUEST._serialized_end=722
  _DATASERVICE._serialized_start=725
  _DATASERVICE._serialized_end=5524
# @@protoc_insertion_point(module_scope)
