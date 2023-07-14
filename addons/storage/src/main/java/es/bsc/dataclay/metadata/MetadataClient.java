package es.bsc.dataclay.metadata;

import io.grpc.Channel;
import io.grpc.Grpc;
import io.grpc.InsecureChannelCredentials;
import io.grpc.ManagedChannel;
import io.grpc.StatusRuntimeException;
import java.util.concurrent.TimeUnit;
import java.util.logging.Level;
import java.util.logging.Logger;

import es.bsc.dataclay.proto.metadata.MetadataServiceGrpc;
import es.bsc.dataclay.proto.metadata.NewAccountRequest;

public class MetadataClient {
  private static final Logger logger = Logger.getLogger(MetadataClient.class.getName());

  private final MetadataServiceGrpc.MetadataServiceBlockingStub blockingStub;
  private final ManagedChannel channel;


  public MetadataClient(String target) {
    channel = Grpc.newChannelBuilder(target, InsecureChannelCredentials.create()).build();
    blockingStub = MetadataServiceGrpc.newBlockingStub(channel);
  }

  public void shutdown() throws InterruptedException {
    channel.shutdown().awaitTermination(5, TimeUnit.SECONDS);
  }

  public void newAccount(String username, String password) {
    logger.info("Will try to create new account " + username + " with password " + password);
    NewAccountRequest request = NewAccountRequest.newBuilder().setUsername(username).setPassword(password).build();
    logger.info(request.toString());
    try {
      blockingStub.newAccount(request);
    } catch (StatusRuntimeException e) {
      logger.log(Level.WARNING, "RPC failed: {0}", e.getStatus());
      return;
    }
    // logger.info("Greeting: " + response.getMessage());
  }

  public static void main(String[] args) throws Exception {
    // Access a service running on the local machine on port 50051
    String target = "127.0.0.1:16587";

    MetadataClient client = new MetadataClient(target);
    try {
      client.newAccount("user", "pass");
    } finally {
      client.shutdown();
    }
  }
}
