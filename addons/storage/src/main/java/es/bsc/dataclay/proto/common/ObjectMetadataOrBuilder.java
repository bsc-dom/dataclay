// Generated by the protocol buffer compiler.  DO NOT EDIT!
// source: dataclay/proto/common/common.proto

package es.bsc.dataclay.proto.common;

public interface ObjectMetadataOrBuilder extends
    // @@protoc_insertion_point(interface_extends:dataclay.proto.common.ObjectMetadata)
    com.google.protobuf.MessageOrBuilder {

  /**
   * <code>string id = 1;</code>
   * @return The id.
   */
  java.lang.String getId();
  /**
   * <code>string id = 1;</code>
   * @return The bytes for id.
   */
  com.google.protobuf.ByteString
      getIdBytes();

  /**
   * <code>string dataset_name = 2;</code>
   * @return The datasetName.
   */
  java.lang.String getDatasetName();
  /**
   * <code>string dataset_name = 2;</code>
   * @return The bytes for datasetName.
   */
  com.google.protobuf.ByteString
      getDatasetNameBytes();

  /**
   * <code>string class_name = 3;</code>
   * @return The className.
   */
  java.lang.String getClassName();
  /**
   * <code>string class_name = 3;</code>
   * @return The bytes for className.
   */
  com.google.protobuf.ByteString
      getClassNameBytes();

  /**
   * <code>string backend_id = 4;</code>
   * @return The backendId.
   */
  java.lang.String getBackendId();
  /**
   * <code>string backend_id = 4;</code>
   * @return The bytes for backendId.
   */
  com.google.protobuf.ByteString
      getBackendIdBytes();

  /**
   * <code>repeated string replica_backend_ids = 5;</code>
   * @return A list containing the replicaBackendIds.
   */
  java.util.List<java.lang.String>
      getReplicaBackendIdsList();
  /**
   * <code>repeated string replica_backend_ids = 5;</code>
   * @return The count of replicaBackendIds.
   */
  int getReplicaBackendIdsCount();
  /**
   * <code>repeated string replica_backend_ids = 5;</code>
   * @param index The index of the element to return.
   * @return The replicaBackendIds at the given index.
   */
  java.lang.String getReplicaBackendIds(int index);
  /**
   * <code>repeated string replica_backend_ids = 5;</code>
   * @param index The index of the value to return.
   * @return The bytes of the replicaBackendIds at the given index.
   */
  com.google.protobuf.ByteString
      getReplicaBackendIdsBytes(int index);

  /**
   * <code>bool is_read_only = 6;</code>
   * @return The isReadOnly.
   */
  boolean getIsReadOnly();

  /**
   * <code>string original_object_id = 7;</code>
   * @return The originalObjectId.
   */
  java.lang.String getOriginalObjectId();
  /**
   * <code>string original_object_id = 7;</code>
   * @return The bytes for originalObjectId.
   */
  com.google.protobuf.ByteString
      getOriginalObjectIdBytes();

  /**
   * <code>repeated string versions_object_ids = 8;</code>
   * @return A list containing the versionsObjectIds.
   */
  java.util.List<java.lang.String>
      getVersionsObjectIdsList();
  /**
   * <code>repeated string versions_object_ids = 8;</code>
   * @return The count of versionsObjectIds.
   */
  int getVersionsObjectIdsCount();
  /**
   * <code>repeated string versions_object_ids = 8;</code>
   * @param index The index of the element to return.
   * @return The versionsObjectIds at the given index.
   */
  java.lang.String getVersionsObjectIds(int index);
  /**
   * <code>repeated string versions_object_ids = 8;</code>
   * @param index The index of the value to return.
   * @return The bytes of the versionsObjectIds at the given index.
   */
  com.google.protobuf.ByteString
      getVersionsObjectIdsBytes(int index);
}
