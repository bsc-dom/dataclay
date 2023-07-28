package es.bsc.dataclay.backend;

import io.grpc.Channel;
import io.grpc.Grpc;
import io.grpc.InsecureChannelCredentials;
import io.grpc.ManagedChannel;
import io.grpc.StatusRuntimeException;
import java.util.concurrent.TimeUnit;
import java.util.logging.Level;
import java.util.logging.Logger;

import es.bsc.dataclay.proto.backend.BackendServiceGrpc;
import es.bsc.dataclay.proto.backend.NewObjectVersionRequest;
import es.bsc.dataclay.proto.backend.NewObjectVersionResponse;
import es.bsc.dataclay.proto.backend.ConsolidateObjectVersionRequest;
import es.bsc.dataclay.proto.backend.NewObjectReplicaRequest;


public class BackendClient {
  private static final Logger logger = Logger.getLogger(BackendClient.class.getName());

  private final BackendServiceGrpc.BackendServiceBlockingStub blockingStub;
  private final ManagedChannel channel;

  public BackendClient(String host, int port) {
    channel = Grpc.newChannelBuilderForAddress(host, port, InsecureChannelCredentials.create()).build();
    blockingStub = BackendServiceGrpc.newBlockingStub(channel);
  }

  public void shutdown() throws InterruptedException {
    channel.shutdown().awaitTermination(5, TimeUnit.SECONDS);
  }

  public String newObjectVersion(String objectId) {
    NewObjectVersionRequest request = NewObjectVersionRequest.newBuilder().setObjectId(objectId).build();
    NewObjectVersionResponse response;
    response = blockingStub.newObjectVersion(request);
    return response.getObjectInfo();
  }

  public void consolidateObjectVersion(String objectId) {
    ConsolidateObjectVersionRequest request = ConsolidateObjectVersionRequest.newBuilder().setObjectId(objectId)
        .build();
    blockingStub.consolidateObjectVersion(request);
  }

  public void newObjectReplica(String objectId, String backendId) {
    NewObjectReplicaRequest request = NewObjectReplicaRequest.newBuilder().setObjectId(objectId).setBackendId(backendId)
        .build();
    blockingStub.newObjectReplica(request);
  }

  public void newObjectReplica(String objectId, String backendId, boolean recursive, boolean remotes) {
    NewObjectReplicaRequest request = NewObjectReplicaRequest.newBuilder().setObjectId(objectId).setBackendId(backendId)
        .setRecursive(recursive).setRemotes(remotes)
        .build();
    blockingStub.newObjectReplica(request);
  }

}
