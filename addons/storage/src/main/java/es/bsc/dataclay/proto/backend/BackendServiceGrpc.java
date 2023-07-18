package es.bsc.dataclay.proto.backend;

import static io.grpc.MethodDescriptor.generateFullMethodName;

/**
 */
@javax.annotation.Generated(
    value = "by gRPC proto compiler (version 1.56.0)",
    comments = "Source: dataclay/proto/backend/backend.proto")
@io.grpc.stub.annotations.GrpcGenerated
public final class BackendServiceGrpc {

  private BackendServiceGrpc() {}

  public static final String SERVICE_NAME = "dataclay.proto.backend.BackendService";

  // Static method descriptors that strictly reflect the proto.
  private static volatile io.grpc.MethodDescriptor<es.bsc.dataclay.proto.backend.MakePersistentRequest,
      com.google.protobuf.Empty> getMakePersistentMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "MakePersistent",
      requestType = es.bsc.dataclay.proto.backend.MakePersistentRequest.class,
      responseType = com.google.protobuf.Empty.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<es.bsc.dataclay.proto.backend.MakePersistentRequest,
      com.google.protobuf.Empty> getMakePersistentMethod() {
    io.grpc.MethodDescriptor<es.bsc.dataclay.proto.backend.MakePersistentRequest, com.google.protobuf.Empty> getMakePersistentMethod;
    if ((getMakePersistentMethod = BackendServiceGrpc.getMakePersistentMethod) == null) {
      synchronized (BackendServiceGrpc.class) {
        if ((getMakePersistentMethod = BackendServiceGrpc.getMakePersistentMethod) == null) {
          BackendServiceGrpc.getMakePersistentMethod = getMakePersistentMethod =
              io.grpc.MethodDescriptor.<es.bsc.dataclay.proto.backend.MakePersistentRequest, com.google.protobuf.Empty>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "MakePersistent"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  es.bsc.dataclay.proto.backend.MakePersistentRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.google.protobuf.Empty.getDefaultInstance()))
              .setSchemaDescriptor(new BackendServiceMethodDescriptorSupplier("MakePersistent"))
              .build();
        }
      }
    }
    return getMakePersistentMethod;
  }

  private static volatile io.grpc.MethodDescriptor<es.bsc.dataclay.proto.backend.CallActiveMethodRequest,
      es.bsc.dataclay.proto.backend.CallActiveMethodResponse> getCallActiveMethodMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "CallActiveMethod",
      requestType = es.bsc.dataclay.proto.backend.CallActiveMethodRequest.class,
      responseType = es.bsc.dataclay.proto.backend.CallActiveMethodResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<es.bsc.dataclay.proto.backend.CallActiveMethodRequest,
      es.bsc.dataclay.proto.backend.CallActiveMethodResponse> getCallActiveMethodMethod() {
    io.grpc.MethodDescriptor<es.bsc.dataclay.proto.backend.CallActiveMethodRequest, es.bsc.dataclay.proto.backend.CallActiveMethodResponse> getCallActiveMethodMethod;
    if ((getCallActiveMethodMethod = BackendServiceGrpc.getCallActiveMethodMethod) == null) {
      synchronized (BackendServiceGrpc.class) {
        if ((getCallActiveMethodMethod = BackendServiceGrpc.getCallActiveMethodMethod) == null) {
          BackendServiceGrpc.getCallActiveMethodMethod = getCallActiveMethodMethod =
              io.grpc.MethodDescriptor.<es.bsc.dataclay.proto.backend.CallActiveMethodRequest, es.bsc.dataclay.proto.backend.CallActiveMethodResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "CallActiveMethod"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  es.bsc.dataclay.proto.backend.CallActiveMethodRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  es.bsc.dataclay.proto.backend.CallActiveMethodResponse.getDefaultInstance()))
              .setSchemaDescriptor(new BackendServiceMethodDescriptorSupplier("CallActiveMethod"))
              .build();
        }
      }
    }
    return getCallActiveMethodMethod;
  }

  private static volatile io.grpc.MethodDescriptor<es.bsc.dataclay.proto.backend.GetObjectPropertiesRequest,
      com.google.protobuf.BytesValue> getGetObjectPropertiesMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "GetObjectProperties",
      requestType = es.bsc.dataclay.proto.backend.GetObjectPropertiesRequest.class,
      responseType = com.google.protobuf.BytesValue.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<es.bsc.dataclay.proto.backend.GetObjectPropertiesRequest,
      com.google.protobuf.BytesValue> getGetObjectPropertiesMethod() {
    io.grpc.MethodDescriptor<es.bsc.dataclay.proto.backend.GetObjectPropertiesRequest, com.google.protobuf.BytesValue> getGetObjectPropertiesMethod;
    if ((getGetObjectPropertiesMethod = BackendServiceGrpc.getGetObjectPropertiesMethod) == null) {
      synchronized (BackendServiceGrpc.class) {
        if ((getGetObjectPropertiesMethod = BackendServiceGrpc.getGetObjectPropertiesMethod) == null) {
          BackendServiceGrpc.getGetObjectPropertiesMethod = getGetObjectPropertiesMethod =
              io.grpc.MethodDescriptor.<es.bsc.dataclay.proto.backend.GetObjectPropertiesRequest, com.google.protobuf.BytesValue>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "GetObjectProperties"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  es.bsc.dataclay.proto.backend.GetObjectPropertiesRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.google.protobuf.BytesValue.getDefaultInstance()))
              .setSchemaDescriptor(new BackendServiceMethodDescriptorSupplier("GetObjectProperties"))
              .build();
        }
      }
    }
    return getGetObjectPropertiesMethod;
  }

  private static volatile io.grpc.MethodDescriptor<es.bsc.dataclay.proto.backend.UpdateObjectPropertiesRequest,
      com.google.protobuf.Empty> getUpdateObjectPropertiesMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "UpdateObjectProperties",
      requestType = es.bsc.dataclay.proto.backend.UpdateObjectPropertiesRequest.class,
      responseType = com.google.protobuf.Empty.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<es.bsc.dataclay.proto.backend.UpdateObjectPropertiesRequest,
      com.google.protobuf.Empty> getUpdateObjectPropertiesMethod() {
    io.grpc.MethodDescriptor<es.bsc.dataclay.proto.backend.UpdateObjectPropertiesRequest, com.google.protobuf.Empty> getUpdateObjectPropertiesMethod;
    if ((getUpdateObjectPropertiesMethod = BackendServiceGrpc.getUpdateObjectPropertiesMethod) == null) {
      synchronized (BackendServiceGrpc.class) {
        if ((getUpdateObjectPropertiesMethod = BackendServiceGrpc.getUpdateObjectPropertiesMethod) == null) {
          BackendServiceGrpc.getUpdateObjectPropertiesMethod = getUpdateObjectPropertiesMethod =
              io.grpc.MethodDescriptor.<es.bsc.dataclay.proto.backend.UpdateObjectPropertiesRequest, com.google.protobuf.Empty>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "UpdateObjectProperties"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  es.bsc.dataclay.proto.backend.UpdateObjectPropertiesRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.google.protobuf.Empty.getDefaultInstance()))
              .setSchemaDescriptor(new BackendServiceMethodDescriptorSupplier("UpdateObjectProperties"))
              .build();
        }
      }
    }
    return getUpdateObjectPropertiesMethod;
  }

  private static volatile io.grpc.MethodDescriptor<es.bsc.dataclay.proto.backend.MoveObjectRequest,
      com.google.protobuf.Empty> getMoveObjectMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "MoveObject",
      requestType = es.bsc.dataclay.proto.backend.MoveObjectRequest.class,
      responseType = com.google.protobuf.Empty.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<es.bsc.dataclay.proto.backend.MoveObjectRequest,
      com.google.protobuf.Empty> getMoveObjectMethod() {
    io.grpc.MethodDescriptor<es.bsc.dataclay.proto.backend.MoveObjectRequest, com.google.protobuf.Empty> getMoveObjectMethod;
    if ((getMoveObjectMethod = BackendServiceGrpc.getMoveObjectMethod) == null) {
      synchronized (BackendServiceGrpc.class) {
        if ((getMoveObjectMethod = BackendServiceGrpc.getMoveObjectMethod) == null) {
          BackendServiceGrpc.getMoveObjectMethod = getMoveObjectMethod =
              io.grpc.MethodDescriptor.<es.bsc.dataclay.proto.backend.MoveObjectRequest, com.google.protobuf.Empty>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "MoveObject"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  es.bsc.dataclay.proto.backend.MoveObjectRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.google.protobuf.Empty.getDefaultInstance()))
              .setSchemaDescriptor(new BackendServiceMethodDescriptorSupplier("MoveObject"))
              .build();
        }
      }
    }
    return getMoveObjectMethod;
  }

  private static volatile io.grpc.MethodDescriptor<es.bsc.dataclay.proto.backend.SendObjectRequest,
      com.google.protobuf.Empty> getSendObjectMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "SendObject",
      requestType = es.bsc.dataclay.proto.backend.SendObjectRequest.class,
      responseType = com.google.protobuf.Empty.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<es.bsc.dataclay.proto.backend.SendObjectRequest,
      com.google.protobuf.Empty> getSendObjectMethod() {
    io.grpc.MethodDescriptor<es.bsc.dataclay.proto.backend.SendObjectRequest, com.google.protobuf.Empty> getSendObjectMethod;
    if ((getSendObjectMethod = BackendServiceGrpc.getSendObjectMethod) == null) {
      synchronized (BackendServiceGrpc.class) {
        if ((getSendObjectMethod = BackendServiceGrpc.getSendObjectMethod) == null) {
          BackendServiceGrpc.getSendObjectMethod = getSendObjectMethod =
              io.grpc.MethodDescriptor.<es.bsc.dataclay.proto.backend.SendObjectRequest, com.google.protobuf.Empty>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "SendObject"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  es.bsc.dataclay.proto.backend.SendObjectRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.google.protobuf.Empty.getDefaultInstance()))
              .setSchemaDescriptor(new BackendServiceMethodDescriptorSupplier("SendObject"))
              .build();
        }
      }
    }
    return getSendObjectMethod;
  }

  private static volatile io.grpc.MethodDescriptor<es.bsc.dataclay.proto.backend.NewObjectVersionRequest,
      es.bsc.dataclay.proto.backend.NewObjectVersionResponse> getNewObjectVersionMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "NewObjectVersion",
      requestType = es.bsc.dataclay.proto.backend.NewObjectVersionRequest.class,
      responseType = es.bsc.dataclay.proto.backend.NewObjectVersionResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<es.bsc.dataclay.proto.backend.NewObjectVersionRequest,
      es.bsc.dataclay.proto.backend.NewObjectVersionResponse> getNewObjectVersionMethod() {
    io.grpc.MethodDescriptor<es.bsc.dataclay.proto.backend.NewObjectVersionRequest, es.bsc.dataclay.proto.backend.NewObjectVersionResponse> getNewObjectVersionMethod;
    if ((getNewObjectVersionMethod = BackendServiceGrpc.getNewObjectVersionMethod) == null) {
      synchronized (BackendServiceGrpc.class) {
        if ((getNewObjectVersionMethod = BackendServiceGrpc.getNewObjectVersionMethod) == null) {
          BackendServiceGrpc.getNewObjectVersionMethod = getNewObjectVersionMethod =
              io.grpc.MethodDescriptor.<es.bsc.dataclay.proto.backend.NewObjectVersionRequest, es.bsc.dataclay.proto.backend.NewObjectVersionResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "NewObjectVersion"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  es.bsc.dataclay.proto.backend.NewObjectVersionRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  es.bsc.dataclay.proto.backend.NewObjectVersionResponse.getDefaultInstance()))
              .setSchemaDescriptor(new BackendServiceMethodDescriptorSupplier("NewObjectVersion"))
              .build();
        }
      }
    }
    return getNewObjectVersionMethod;
  }

  private static volatile io.grpc.MethodDescriptor<es.bsc.dataclay.proto.backend.ConsolidateObjectVersionRequest,
      com.google.protobuf.Empty> getConsolidateObjectVersionMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "ConsolidateObjectVersion",
      requestType = es.bsc.dataclay.proto.backend.ConsolidateObjectVersionRequest.class,
      responseType = com.google.protobuf.Empty.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<es.bsc.dataclay.proto.backend.ConsolidateObjectVersionRequest,
      com.google.protobuf.Empty> getConsolidateObjectVersionMethod() {
    io.grpc.MethodDescriptor<es.bsc.dataclay.proto.backend.ConsolidateObjectVersionRequest, com.google.protobuf.Empty> getConsolidateObjectVersionMethod;
    if ((getConsolidateObjectVersionMethod = BackendServiceGrpc.getConsolidateObjectVersionMethod) == null) {
      synchronized (BackendServiceGrpc.class) {
        if ((getConsolidateObjectVersionMethod = BackendServiceGrpc.getConsolidateObjectVersionMethod) == null) {
          BackendServiceGrpc.getConsolidateObjectVersionMethod = getConsolidateObjectVersionMethod =
              io.grpc.MethodDescriptor.<es.bsc.dataclay.proto.backend.ConsolidateObjectVersionRequest, com.google.protobuf.Empty>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "ConsolidateObjectVersion"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  es.bsc.dataclay.proto.backend.ConsolidateObjectVersionRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.google.protobuf.Empty.getDefaultInstance()))
              .setSchemaDescriptor(new BackendServiceMethodDescriptorSupplier("ConsolidateObjectVersion"))
              .build();
        }
      }
    }
    return getConsolidateObjectVersionMethod;
  }

  private static volatile io.grpc.MethodDescriptor<es.bsc.dataclay.proto.backend.ProxifyObjectRequest,
      com.google.protobuf.Empty> getProxifyObjectMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "ProxifyObject",
      requestType = es.bsc.dataclay.proto.backend.ProxifyObjectRequest.class,
      responseType = com.google.protobuf.Empty.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<es.bsc.dataclay.proto.backend.ProxifyObjectRequest,
      com.google.protobuf.Empty> getProxifyObjectMethod() {
    io.grpc.MethodDescriptor<es.bsc.dataclay.proto.backend.ProxifyObjectRequest, com.google.protobuf.Empty> getProxifyObjectMethod;
    if ((getProxifyObjectMethod = BackendServiceGrpc.getProxifyObjectMethod) == null) {
      synchronized (BackendServiceGrpc.class) {
        if ((getProxifyObjectMethod = BackendServiceGrpc.getProxifyObjectMethod) == null) {
          BackendServiceGrpc.getProxifyObjectMethod = getProxifyObjectMethod =
              io.grpc.MethodDescriptor.<es.bsc.dataclay.proto.backend.ProxifyObjectRequest, com.google.protobuf.Empty>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "ProxifyObject"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  es.bsc.dataclay.proto.backend.ProxifyObjectRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.google.protobuf.Empty.getDefaultInstance()))
              .setSchemaDescriptor(new BackendServiceMethodDescriptorSupplier("ProxifyObject"))
              .build();
        }
      }
    }
    return getProxifyObjectMethod;
  }

  private static volatile io.grpc.MethodDescriptor<es.bsc.dataclay.proto.backend.ChangeObjectIdRequest,
      com.google.protobuf.Empty> getChangeObjectIdMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "ChangeObjectId",
      requestType = es.bsc.dataclay.proto.backend.ChangeObjectIdRequest.class,
      responseType = com.google.protobuf.Empty.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<es.bsc.dataclay.proto.backend.ChangeObjectIdRequest,
      com.google.protobuf.Empty> getChangeObjectIdMethod() {
    io.grpc.MethodDescriptor<es.bsc.dataclay.proto.backend.ChangeObjectIdRequest, com.google.protobuf.Empty> getChangeObjectIdMethod;
    if ((getChangeObjectIdMethod = BackendServiceGrpc.getChangeObjectIdMethod) == null) {
      synchronized (BackendServiceGrpc.class) {
        if ((getChangeObjectIdMethod = BackendServiceGrpc.getChangeObjectIdMethod) == null) {
          BackendServiceGrpc.getChangeObjectIdMethod = getChangeObjectIdMethod =
              io.grpc.MethodDescriptor.<es.bsc.dataclay.proto.backend.ChangeObjectIdRequest, com.google.protobuf.Empty>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "ChangeObjectId"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  es.bsc.dataclay.proto.backend.ChangeObjectIdRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.google.protobuf.Empty.getDefaultInstance()))
              .setSchemaDescriptor(new BackendServiceMethodDescriptorSupplier("ChangeObjectId"))
              .build();
        }
      }
    }
    return getChangeObjectIdMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.google.protobuf.Empty,
      com.google.protobuf.Empty> getFlushAllMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "FlushAll",
      requestType = com.google.protobuf.Empty.class,
      responseType = com.google.protobuf.Empty.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.google.protobuf.Empty,
      com.google.protobuf.Empty> getFlushAllMethod() {
    io.grpc.MethodDescriptor<com.google.protobuf.Empty, com.google.protobuf.Empty> getFlushAllMethod;
    if ((getFlushAllMethod = BackendServiceGrpc.getFlushAllMethod) == null) {
      synchronized (BackendServiceGrpc.class) {
        if ((getFlushAllMethod = BackendServiceGrpc.getFlushAllMethod) == null) {
          BackendServiceGrpc.getFlushAllMethod = getFlushAllMethod =
              io.grpc.MethodDescriptor.<com.google.protobuf.Empty, com.google.protobuf.Empty>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "FlushAll"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.google.protobuf.Empty.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.google.protobuf.Empty.getDefaultInstance()))
              .setSchemaDescriptor(new BackendServiceMethodDescriptorSupplier("FlushAll"))
              .build();
        }
      }
    }
    return getFlushAllMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.google.protobuf.Empty,
      com.google.protobuf.Empty> getShutdownMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "Shutdown",
      requestType = com.google.protobuf.Empty.class,
      responseType = com.google.protobuf.Empty.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.google.protobuf.Empty,
      com.google.protobuf.Empty> getShutdownMethod() {
    io.grpc.MethodDescriptor<com.google.protobuf.Empty, com.google.protobuf.Empty> getShutdownMethod;
    if ((getShutdownMethod = BackendServiceGrpc.getShutdownMethod) == null) {
      synchronized (BackendServiceGrpc.class) {
        if ((getShutdownMethod = BackendServiceGrpc.getShutdownMethod) == null) {
          BackendServiceGrpc.getShutdownMethod = getShutdownMethod =
              io.grpc.MethodDescriptor.<com.google.protobuf.Empty, com.google.protobuf.Empty>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "Shutdown"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.google.protobuf.Empty.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.google.protobuf.Empty.getDefaultInstance()))
              .setSchemaDescriptor(new BackendServiceMethodDescriptorSupplier("Shutdown"))
              .build();
        }
      }
    }
    return getShutdownMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.google.protobuf.Empty,
      com.google.protobuf.Empty> getDrainMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "Drain",
      requestType = com.google.protobuf.Empty.class,
      responseType = com.google.protobuf.Empty.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.google.protobuf.Empty,
      com.google.protobuf.Empty> getDrainMethod() {
    io.grpc.MethodDescriptor<com.google.protobuf.Empty, com.google.protobuf.Empty> getDrainMethod;
    if ((getDrainMethod = BackendServiceGrpc.getDrainMethod) == null) {
      synchronized (BackendServiceGrpc.class) {
        if ((getDrainMethod = BackendServiceGrpc.getDrainMethod) == null) {
          BackendServiceGrpc.getDrainMethod = getDrainMethod =
              io.grpc.MethodDescriptor.<com.google.protobuf.Empty, com.google.protobuf.Empty>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "Drain"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.google.protobuf.Empty.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.google.protobuf.Empty.getDefaultInstance()))
              .setSchemaDescriptor(new BackendServiceMethodDescriptorSupplier("Drain"))
              .build();
        }
      }
    }
    return getDrainMethod;
  }

  /**
   * Creates a new async stub that supports all call types for the service
   */
  public static BackendServiceStub newStub(io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<BackendServiceStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<BackendServiceStub>() {
        @java.lang.Override
        public BackendServiceStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new BackendServiceStub(channel, callOptions);
        }
      };
    return BackendServiceStub.newStub(factory, channel);
  }

  /**
   * Creates a new blocking-style stub that supports unary and streaming output calls on the service
   */
  public static BackendServiceBlockingStub newBlockingStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<BackendServiceBlockingStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<BackendServiceBlockingStub>() {
        @java.lang.Override
        public BackendServiceBlockingStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new BackendServiceBlockingStub(channel, callOptions);
        }
      };
    return BackendServiceBlockingStub.newStub(factory, channel);
  }

  /**
   * Creates a new ListenableFuture-style stub that supports unary calls on the service
   */
  public static BackendServiceFutureStub newFutureStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<BackendServiceFutureStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<BackendServiceFutureStub>() {
        @java.lang.Override
        public BackendServiceFutureStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new BackendServiceFutureStub(channel, callOptions);
        }
      };
    return BackendServiceFutureStub.newStub(factory, channel);
  }

  /**
   */
  public interface AsyncService {

    /**
     */
    default void makePersistent(es.bsc.dataclay.proto.backend.MakePersistentRequest request,
        io.grpc.stub.StreamObserver<com.google.protobuf.Empty> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getMakePersistentMethod(), responseObserver);
    }

    /**
     */
    default void callActiveMethod(es.bsc.dataclay.proto.backend.CallActiveMethodRequest request,
        io.grpc.stub.StreamObserver<es.bsc.dataclay.proto.backend.CallActiveMethodResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getCallActiveMethodMethod(), responseObserver);
    }

    /**
     */
    default void getObjectProperties(es.bsc.dataclay.proto.backend.GetObjectPropertiesRequest request,
        io.grpc.stub.StreamObserver<com.google.protobuf.BytesValue> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getGetObjectPropertiesMethod(), responseObserver);
    }

    /**
     */
    default void updateObjectProperties(es.bsc.dataclay.proto.backend.UpdateObjectPropertiesRequest request,
        io.grpc.stub.StreamObserver<com.google.protobuf.Empty> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getUpdateObjectPropertiesMethod(), responseObserver);
    }

    /**
     */
    default void moveObject(es.bsc.dataclay.proto.backend.MoveObjectRequest request,
        io.grpc.stub.StreamObserver<com.google.protobuf.Empty> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getMoveObjectMethod(), responseObserver);
    }

    /**
     */
    default void sendObject(es.bsc.dataclay.proto.backend.SendObjectRequest request,
        io.grpc.stub.StreamObserver<com.google.protobuf.Empty> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getSendObjectMethod(), responseObserver);
    }

    /**
     */
    default void newObjectVersion(es.bsc.dataclay.proto.backend.NewObjectVersionRequest request,
        io.grpc.stub.StreamObserver<es.bsc.dataclay.proto.backend.NewObjectVersionResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getNewObjectVersionMethod(), responseObserver);
    }

    /**
     */
    default void consolidateObjectVersion(es.bsc.dataclay.proto.backend.ConsolidateObjectVersionRequest request,
        io.grpc.stub.StreamObserver<com.google.protobuf.Empty> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getConsolidateObjectVersionMethod(), responseObserver);
    }

    /**
     */
    default void proxifyObject(es.bsc.dataclay.proto.backend.ProxifyObjectRequest request,
        io.grpc.stub.StreamObserver<com.google.protobuf.Empty> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getProxifyObjectMethod(), responseObserver);
    }

    /**
     */
    default void changeObjectId(es.bsc.dataclay.proto.backend.ChangeObjectIdRequest request,
        io.grpc.stub.StreamObserver<com.google.protobuf.Empty> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getChangeObjectIdMethod(), responseObserver);
    }

    /**
     */
    default void flushAll(com.google.protobuf.Empty request,
        io.grpc.stub.StreamObserver<com.google.protobuf.Empty> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getFlushAllMethod(), responseObserver);
    }

    /**
     */
    default void shutdown(com.google.protobuf.Empty request,
        io.grpc.stub.StreamObserver<com.google.protobuf.Empty> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getShutdownMethod(), responseObserver);
    }

    /**
     */
    default void drain(com.google.protobuf.Empty request,
        io.grpc.stub.StreamObserver<com.google.protobuf.Empty> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getDrainMethod(), responseObserver);
    }
  }

  /**
   * Base class for the server implementation of the service BackendService.
   */
  public static abstract class BackendServiceImplBase
      implements io.grpc.BindableService, AsyncService {

    @java.lang.Override public final io.grpc.ServerServiceDefinition bindService() {
      return BackendServiceGrpc.bindService(this);
    }
  }

  /**
   * A stub to allow clients to do asynchronous rpc calls to service BackendService.
   */
  public static final class BackendServiceStub
      extends io.grpc.stub.AbstractAsyncStub<BackendServiceStub> {
    private BackendServiceStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected BackendServiceStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new BackendServiceStub(channel, callOptions);
    }

    /**
     */
    public void makePersistent(es.bsc.dataclay.proto.backend.MakePersistentRequest request,
        io.grpc.stub.StreamObserver<com.google.protobuf.Empty> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getMakePersistentMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void callActiveMethod(es.bsc.dataclay.proto.backend.CallActiveMethodRequest request,
        io.grpc.stub.StreamObserver<es.bsc.dataclay.proto.backend.CallActiveMethodResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getCallActiveMethodMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void getObjectProperties(es.bsc.dataclay.proto.backend.GetObjectPropertiesRequest request,
        io.grpc.stub.StreamObserver<com.google.protobuf.BytesValue> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getGetObjectPropertiesMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void updateObjectProperties(es.bsc.dataclay.proto.backend.UpdateObjectPropertiesRequest request,
        io.grpc.stub.StreamObserver<com.google.protobuf.Empty> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getUpdateObjectPropertiesMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void moveObject(es.bsc.dataclay.proto.backend.MoveObjectRequest request,
        io.grpc.stub.StreamObserver<com.google.protobuf.Empty> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getMoveObjectMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void sendObject(es.bsc.dataclay.proto.backend.SendObjectRequest request,
        io.grpc.stub.StreamObserver<com.google.protobuf.Empty> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getSendObjectMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void newObjectVersion(es.bsc.dataclay.proto.backend.NewObjectVersionRequest request,
        io.grpc.stub.StreamObserver<es.bsc.dataclay.proto.backend.NewObjectVersionResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getNewObjectVersionMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void consolidateObjectVersion(es.bsc.dataclay.proto.backend.ConsolidateObjectVersionRequest request,
        io.grpc.stub.StreamObserver<com.google.protobuf.Empty> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getConsolidateObjectVersionMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void proxifyObject(es.bsc.dataclay.proto.backend.ProxifyObjectRequest request,
        io.grpc.stub.StreamObserver<com.google.protobuf.Empty> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getProxifyObjectMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void changeObjectId(es.bsc.dataclay.proto.backend.ChangeObjectIdRequest request,
        io.grpc.stub.StreamObserver<com.google.protobuf.Empty> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getChangeObjectIdMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void flushAll(com.google.protobuf.Empty request,
        io.grpc.stub.StreamObserver<com.google.protobuf.Empty> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getFlushAllMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void shutdown(com.google.protobuf.Empty request,
        io.grpc.stub.StreamObserver<com.google.protobuf.Empty> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getShutdownMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void drain(com.google.protobuf.Empty request,
        io.grpc.stub.StreamObserver<com.google.protobuf.Empty> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getDrainMethod(), getCallOptions()), request, responseObserver);
    }
  }

  /**
   * A stub to allow clients to do synchronous rpc calls to service BackendService.
   */
  public static final class BackendServiceBlockingStub
      extends io.grpc.stub.AbstractBlockingStub<BackendServiceBlockingStub> {
    private BackendServiceBlockingStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected BackendServiceBlockingStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new BackendServiceBlockingStub(channel, callOptions);
    }

    /**
     */
    public com.google.protobuf.Empty makePersistent(es.bsc.dataclay.proto.backend.MakePersistentRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getMakePersistentMethod(), getCallOptions(), request);
    }

    /**
     */
    public es.bsc.dataclay.proto.backend.CallActiveMethodResponse callActiveMethod(es.bsc.dataclay.proto.backend.CallActiveMethodRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getCallActiveMethodMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.google.protobuf.BytesValue getObjectProperties(es.bsc.dataclay.proto.backend.GetObjectPropertiesRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getGetObjectPropertiesMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.google.protobuf.Empty updateObjectProperties(es.bsc.dataclay.proto.backend.UpdateObjectPropertiesRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getUpdateObjectPropertiesMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.google.protobuf.Empty moveObject(es.bsc.dataclay.proto.backend.MoveObjectRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getMoveObjectMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.google.protobuf.Empty sendObject(es.bsc.dataclay.proto.backend.SendObjectRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getSendObjectMethod(), getCallOptions(), request);
    }

    /**
     */
    public es.bsc.dataclay.proto.backend.NewObjectVersionResponse newObjectVersion(es.bsc.dataclay.proto.backend.NewObjectVersionRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getNewObjectVersionMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.google.protobuf.Empty consolidateObjectVersion(es.bsc.dataclay.proto.backend.ConsolidateObjectVersionRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getConsolidateObjectVersionMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.google.protobuf.Empty proxifyObject(es.bsc.dataclay.proto.backend.ProxifyObjectRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getProxifyObjectMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.google.protobuf.Empty changeObjectId(es.bsc.dataclay.proto.backend.ChangeObjectIdRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getChangeObjectIdMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.google.protobuf.Empty flushAll(com.google.protobuf.Empty request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getFlushAllMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.google.protobuf.Empty shutdown(com.google.protobuf.Empty request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getShutdownMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.google.protobuf.Empty drain(com.google.protobuf.Empty request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getDrainMethod(), getCallOptions(), request);
    }
  }

  /**
   * A stub to allow clients to do ListenableFuture-style rpc calls to service BackendService.
   */
  public static final class BackendServiceFutureStub
      extends io.grpc.stub.AbstractFutureStub<BackendServiceFutureStub> {
    private BackendServiceFutureStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected BackendServiceFutureStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new BackendServiceFutureStub(channel, callOptions);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.google.protobuf.Empty> makePersistent(
        es.bsc.dataclay.proto.backend.MakePersistentRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getMakePersistentMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<es.bsc.dataclay.proto.backend.CallActiveMethodResponse> callActiveMethod(
        es.bsc.dataclay.proto.backend.CallActiveMethodRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getCallActiveMethodMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.google.protobuf.BytesValue> getObjectProperties(
        es.bsc.dataclay.proto.backend.GetObjectPropertiesRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getGetObjectPropertiesMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.google.protobuf.Empty> updateObjectProperties(
        es.bsc.dataclay.proto.backend.UpdateObjectPropertiesRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getUpdateObjectPropertiesMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.google.protobuf.Empty> moveObject(
        es.bsc.dataclay.proto.backend.MoveObjectRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getMoveObjectMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.google.protobuf.Empty> sendObject(
        es.bsc.dataclay.proto.backend.SendObjectRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getSendObjectMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<es.bsc.dataclay.proto.backend.NewObjectVersionResponse> newObjectVersion(
        es.bsc.dataclay.proto.backend.NewObjectVersionRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getNewObjectVersionMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.google.protobuf.Empty> consolidateObjectVersion(
        es.bsc.dataclay.proto.backend.ConsolidateObjectVersionRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getConsolidateObjectVersionMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.google.protobuf.Empty> proxifyObject(
        es.bsc.dataclay.proto.backend.ProxifyObjectRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getProxifyObjectMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.google.protobuf.Empty> changeObjectId(
        es.bsc.dataclay.proto.backend.ChangeObjectIdRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getChangeObjectIdMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.google.protobuf.Empty> flushAll(
        com.google.protobuf.Empty request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getFlushAllMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.google.protobuf.Empty> shutdown(
        com.google.protobuf.Empty request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getShutdownMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.google.protobuf.Empty> drain(
        com.google.protobuf.Empty request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getDrainMethod(), getCallOptions()), request);
    }
  }

  private static final int METHODID_MAKE_PERSISTENT = 0;
  private static final int METHODID_CALL_ACTIVE_METHOD = 1;
  private static final int METHODID_GET_OBJECT_PROPERTIES = 2;
  private static final int METHODID_UPDATE_OBJECT_PROPERTIES = 3;
  private static final int METHODID_MOVE_OBJECT = 4;
  private static final int METHODID_SEND_OBJECT = 5;
  private static final int METHODID_NEW_OBJECT_VERSION = 6;
  private static final int METHODID_CONSOLIDATE_OBJECT_VERSION = 7;
  private static final int METHODID_PROXIFY_OBJECT = 8;
  private static final int METHODID_CHANGE_OBJECT_ID = 9;
  private static final int METHODID_FLUSH_ALL = 10;
  private static final int METHODID_SHUTDOWN = 11;
  private static final int METHODID_DRAIN = 12;

  private static final class MethodHandlers<Req, Resp> implements
      io.grpc.stub.ServerCalls.UnaryMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.ServerStreamingMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.ClientStreamingMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.BidiStreamingMethod<Req, Resp> {
    private final AsyncService serviceImpl;
    private final int methodId;

    MethodHandlers(AsyncService serviceImpl, int methodId) {
      this.serviceImpl = serviceImpl;
      this.methodId = methodId;
    }

    @java.lang.Override
    @java.lang.SuppressWarnings("unchecked")
    public void invoke(Req request, io.grpc.stub.StreamObserver<Resp> responseObserver) {
      switch (methodId) {
        case METHODID_MAKE_PERSISTENT:
          serviceImpl.makePersistent((es.bsc.dataclay.proto.backend.MakePersistentRequest) request,
              (io.grpc.stub.StreamObserver<com.google.protobuf.Empty>) responseObserver);
          break;
        case METHODID_CALL_ACTIVE_METHOD:
          serviceImpl.callActiveMethod((es.bsc.dataclay.proto.backend.CallActiveMethodRequest) request,
              (io.grpc.stub.StreamObserver<es.bsc.dataclay.proto.backend.CallActiveMethodResponse>) responseObserver);
          break;
        case METHODID_GET_OBJECT_PROPERTIES:
          serviceImpl.getObjectProperties((es.bsc.dataclay.proto.backend.GetObjectPropertiesRequest) request,
              (io.grpc.stub.StreamObserver<com.google.protobuf.BytesValue>) responseObserver);
          break;
        case METHODID_UPDATE_OBJECT_PROPERTIES:
          serviceImpl.updateObjectProperties((es.bsc.dataclay.proto.backend.UpdateObjectPropertiesRequest) request,
              (io.grpc.stub.StreamObserver<com.google.protobuf.Empty>) responseObserver);
          break;
        case METHODID_MOVE_OBJECT:
          serviceImpl.moveObject((es.bsc.dataclay.proto.backend.MoveObjectRequest) request,
              (io.grpc.stub.StreamObserver<com.google.protobuf.Empty>) responseObserver);
          break;
        case METHODID_SEND_OBJECT:
          serviceImpl.sendObject((es.bsc.dataclay.proto.backend.SendObjectRequest) request,
              (io.grpc.stub.StreamObserver<com.google.protobuf.Empty>) responseObserver);
          break;
        case METHODID_NEW_OBJECT_VERSION:
          serviceImpl.newObjectVersion((es.bsc.dataclay.proto.backend.NewObjectVersionRequest) request,
              (io.grpc.stub.StreamObserver<es.bsc.dataclay.proto.backend.NewObjectVersionResponse>) responseObserver);
          break;
        case METHODID_CONSOLIDATE_OBJECT_VERSION:
          serviceImpl.consolidateObjectVersion((es.bsc.dataclay.proto.backend.ConsolidateObjectVersionRequest) request,
              (io.grpc.stub.StreamObserver<com.google.protobuf.Empty>) responseObserver);
          break;
        case METHODID_PROXIFY_OBJECT:
          serviceImpl.proxifyObject((es.bsc.dataclay.proto.backend.ProxifyObjectRequest) request,
              (io.grpc.stub.StreamObserver<com.google.protobuf.Empty>) responseObserver);
          break;
        case METHODID_CHANGE_OBJECT_ID:
          serviceImpl.changeObjectId((es.bsc.dataclay.proto.backend.ChangeObjectIdRequest) request,
              (io.grpc.stub.StreamObserver<com.google.protobuf.Empty>) responseObserver);
          break;
        case METHODID_FLUSH_ALL:
          serviceImpl.flushAll((com.google.protobuf.Empty) request,
              (io.grpc.stub.StreamObserver<com.google.protobuf.Empty>) responseObserver);
          break;
        case METHODID_SHUTDOWN:
          serviceImpl.shutdown((com.google.protobuf.Empty) request,
              (io.grpc.stub.StreamObserver<com.google.protobuf.Empty>) responseObserver);
          break;
        case METHODID_DRAIN:
          serviceImpl.drain((com.google.protobuf.Empty) request,
              (io.grpc.stub.StreamObserver<com.google.protobuf.Empty>) responseObserver);
          break;
        default:
          throw new AssertionError();
      }
    }

    @java.lang.Override
    @java.lang.SuppressWarnings("unchecked")
    public io.grpc.stub.StreamObserver<Req> invoke(
        io.grpc.stub.StreamObserver<Resp> responseObserver) {
      switch (methodId) {
        default:
          throw new AssertionError();
      }
    }
  }

  public static final io.grpc.ServerServiceDefinition bindService(AsyncService service) {
    return io.grpc.ServerServiceDefinition.builder(getServiceDescriptor())
        .addMethod(
          getMakePersistentMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              es.bsc.dataclay.proto.backend.MakePersistentRequest,
              com.google.protobuf.Empty>(
                service, METHODID_MAKE_PERSISTENT)))
        .addMethod(
          getCallActiveMethodMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              es.bsc.dataclay.proto.backend.CallActiveMethodRequest,
              es.bsc.dataclay.proto.backend.CallActiveMethodResponse>(
                service, METHODID_CALL_ACTIVE_METHOD)))
        .addMethod(
          getGetObjectPropertiesMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              es.bsc.dataclay.proto.backend.GetObjectPropertiesRequest,
              com.google.protobuf.BytesValue>(
                service, METHODID_GET_OBJECT_PROPERTIES)))
        .addMethod(
          getUpdateObjectPropertiesMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              es.bsc.dataclay.proto.backend.UpdateObjectPropertiesRequest,
              com.google.protobuf.Empty>(
                service, METHODID_UPDATE_OBJECT_PROPERTIES)))
        .addMethod(
          getMoveObjectMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              es.bsc.dataclay.proto.backend.MoveObjectRequest,
              com.google.protobuf.Empty>(
                service, METHODID_MOVE_OBJECT)))
        .addMethod(
          getSendObjectMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              es.bsc.dataclay.proto.backend.SendObjectRequest,
              com.google.protobuf.Empty>(
                service, METHODID_SEND_OBJECT)))
        .addMethod(
          getNewObjectVersionMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              es.bsc.dataclay.proto.backend.NewObjectVersionRequest,
              es.bsc.dataclay.proto.backend.NewObjectVersionResponse>(
                service, METHODID_NEW_OBJECT_VERSION)))
        .addMethod(
          getConsolidateObjectVersionMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              es.bsc.dataclay.proto.backend.ConsolidateObjectVersionRequest,
              com.google.protobuf.Empty>(
                service, METHODID_CONSOLIDATE_OBJECT_VERSION)))
        .addMethod(
          getProxifyObjectMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              es.bsc.dataclay.proto.backend.ProxifyObjectRequest,
              com.google.protobuf.Empty>(
                service, METHODID_PROXIFY_OBJECT)))
        .addMethod(
          getChangeObjectIdMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              es.bsc.dataclay.proto.backend.ChangeObjectIdRequest,
              com.google.protobuf.Empty>(
                service, METHODID_CHANGE_OBJECT_ID)))
        .addMethod(
          getFlushAllMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.google.protobuf.Empty,
              com.google.protobuf.Empty>(
                service, METHODID_FLUSH_ALL)))
        .addMethod(
          getShutdownMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.google.protobuf.Empty,
              com.google.protobuf.Empty>(
                service, METHODID_SHUTDOWN)))
        .addMethod(
          getDrainMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.google.protobuf.Empty,
              com.google.protobuf.Empty>(
                service, METHODID_DRAIN)))
        .build();
  }

  private static abstract class BackendServiceBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoFileDescriptorSupplier, io.grpc.protobuf.ProtoServiceDescriptorSupplier {
    BackendServiceBaseDescriptorSupplier() {}

    @java.lang.Override
    public com.google.protobuf.Descriptors.FileDescriptor getFileDescriptor() {
      return es.bsc.dataclay.proto.backend.Backend.getDescriptor();
    }

    @java.lang.Override
    public com.google.protobuf.Descriptors.ServiceDescriptor getServiceDescriptor() {
      return getFileDescriptor().findServiceByName("BackendService");
    }
  }

  private static final class BackendServiceFileDescriptorSupplier
      extends BackendServiceBaseDescriptorSupplier {
    BackendServiceFileDescriptorSupplier() {}
  }

  private static final class BackendServiceMethodDescriptorSupplier
      extends BackendServiceBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoMethodDescriptorSupplier {
    private final String methodName;

    BackendServiceMethodDescriptorSupplier(String methodName) {
      this.methodName = methodName;
    }

    @java.lang.Override
    public com.google.protobuf.Descriptors.MethodDescriptor getMethodDescriptor() {
      return getServiceDescriptor().findMethodByName(methodName);
    }
  }

  private static volatile io.grpc.ServiceDescriptor serviceDescriptor;

  public static io.grpc.ServiceDescriptor getServiceDescriptor() {
    io.grpc.ServiceDescriptor result = serviceDescriptor;
    if (result == null) {
      synchronized (BackendServiceGrpc.class) {
        result = serviceDescriptor;
        if (result == null) {
          serviceDescriptor = result = io.grpc.ServiceDescriptor.newBuilder(SERVICE_NAME)
              .setSchemaDescriptor(new BackendServiceFileDescriptorSupplier())
              .addMethod(getMakePersistentMethod())
              .addMethod(getCallActiveMethodMethod())
              .addMethod(getGetObjectPropertiesMethod())
              .addMethod(getUpdateObjectPropertiesMethod())
              .addMethod(getMoveObjectMethod())
              .addMethod(getSendObjectMethod())
              .addMethod(getNewObjectVersionMethod())
              .addMethod(getConsolidateObjectVersionMethod())
              .addMethod(getProxifyObjectMethod())
              .addMethod(getChangeObjectIdMethod())
              .addMethod(getFlushAllMethod())
              .addMethod(getShutdownMethod())
              .addMethod(getDrainMethod())
              .build();
        }
      }
    }
    return result;
  }
}
