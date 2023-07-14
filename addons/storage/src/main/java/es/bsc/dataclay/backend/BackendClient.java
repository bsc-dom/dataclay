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

  public static void main(String[] args) throws Exception {
    // Access a service running on the local machine on port 50051
    BackendClient client = new BackendClient("127.0.0.1", 16587);
    try {
      // client.newAccount("user", "pass");
    } finally {
      client.shutdown();
    }
  }
}
