package es.bsc.dataclay.proto.metadata;

import static io.grpc.MethodDescriptor.generateFullMethodName;

/**
 */
@javax.annotation.Generated(
    value = "by gRPC proto compiler (version 1.56.0)",
    comments = "Source: dataclay/proto/metadata/metadata.proto")
@io.grpc.stub.annotations.GrpcGenerated
public final class MetadataServiceGrpc {

  private MetadataServiceGrpc() {}

  public static final String SERVICE_NAME = "dataclay.proto.metadata.MetadataService";

  // Static method descriptors that strictly reflect the proto.
  private static volatile io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.NewAccountRequest,
      com.google.protobuf.Empty> getNewAccountMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "NewAccount",
      requestType = es.bsc.dataclay.proto.metadata.NewAccountRequest.class,
      responseType = com.google.protobuf.Empty.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.NewAccountRequest,
      com.google.protobuf.Empty> getNewAccountMethod() {
    io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.NewAccountRequest, com.google.protobuf.Empty> getNewAccountMethod;
    if ((getNewAccountMethod = MetadataServiceGrpc.getNewAccountMethod) == null) {
      synchronized (MetadataServiceGrpc.class) {
        if ((getNewAccountMethod = MetadataServiceGrpc.getNewAccountMethod) == null) {
          MetadataServiceGrpc.getNewAccountMethod = getNewAccountMethod =
              io.grpc.MethodDescriptor.<es.bsc.dataclay.proto.metadata.NewAccountRequest, com.google.protobuf.Empty>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "NewAccount"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  es.bsc.dataclay.proto.metadata.NewAccountRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.google.protobuf.Empty.getDefaultInstance()))
              .setSchemaDescriptor(new MetadataServiceMethodDescriptorSupplier("NewAccount"))
              .build();
        }
      }
    }
    return getNewAccountMethod;
  }

  private static volatile io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.GetAccountRequest,
      es.bsc.dataclay.proto.metadata.GetAccountResponse> getGetAccountMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "GetAccount",
      requestType = es.bsc.dataclay.proto.metadata.GetAccountRequest.class,
      responseType = es.bsc.dataclay.proto.metadata.GetAccountResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.GetAccountRequest,
      es.bsc.dataclay.proto.metadata.GetAccountResponse> getGetAccountMethod() {
    io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.GetAccountRequest, es.bsc.dataclay.proto.metadata.GetAccountResponse> getGetAccountMethod;
    if ((getGetAccountMethod = MetadataServiceGrpc.getGetAccountMethod) == null) {
      synchronized (MetadataServiceGrpc.class) {
        if ((getGetAccountMethod = MetadataServiceGrpc.getGetAccountMethod) == null) {
          MetadataServiceGrpc.getGetAccountMethod = getGetAccountMethod =
              io.grpc.MethodDescriptor.<es.bsc.dataclay.proto.metadata.GetAccountRequest, es.bsc.dataclay.proto.metadata.GetAccountResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "GetAccount"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  es.bsc.dataclay.proto.metadata.GetAccountRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  es.bsc.dataclay.proto.metadata.GetAccountResponse.getDefaultInstance()))
              .setSchemaDescriptor(new MetadataServiceMethodDescriptorSupplier("GetAccount"))
              .build();
        }
      }
    }
    return getGetAccountMethod;
  }

  private static volatile io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.NewSessionRequest,
      es.bsc.dataclay.proto.common.Session> getNewSessionMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "NewSession",
      requestType = es.bsc.dataclay.proto.metadata.NewSessionRequest.class,
      responseType = es.bsc.dataclay.proto.common.Session.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.NewSessionRequest,
      es.bsc.dataclay.proto.common.Session> getNewSessionMethod() {
    io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.NewSessionRequest, es.bsc.dataclay.proto.common.Session> getNewSessionMethod;
    if ((getNewSessionMethod = MetadataServiceGrpc.getNewSessionMethod) == null) {
      synchronized (MetadataServiceGrpc.class) {
        if ((getNewSessionMethod = MetadataServiceGrpc.getNewSessionMethod) == null) {
          MetadataServiceGrpc.getNewSessionMethod = getNewSessionMethod =
              io.grpc.MethodDescriptor.<es.bsc.dataclay.proto.metadata.NewSessionRequest, es.bsc.dataclay.proto.common.Session>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "NewSession"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  es.bsc.dataclay.proto.metadata.NewSessionRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  es.bsc.dataclay.proto.common.Session.getDefaultInstance()))
              .setSchemaDescriptor(new MetadataServiceMethodDescriptorSupplier("NewSession"))
              .build();
        }
      }
    }
    return getNewSessionMethod;
  }

  private static volatile io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.CloseSessionRequest,
      com.google.protobuf.Empty> getCloseSessionMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "CloseSession",
      requestType = es.bsc.dataclay.proto.metadata.CloseSessionRequest.class,
      responseType = com.google.protobuf.Empty.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.CloseSessionRequest,
      com.google.protobuf.Empty> getCloseSessionMethod() {
    io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.CloseSessionRequest, com.google.protobuf.Empty> getCloseSessionMethod;
    if ((getCloseSessionMethod = MetadataServiceGrpc.getCloseSessionMethod) == null) {
      synchronized (MetadataServiceGrpc.class) {
        if ((getCloseSessionMethod = MetadataServiceGrpc.getCloseSessionMethod) == null) {
          MetadataServiceGrpc.getCloseSessionMethod = getCloseSessionMethod =
              io.grpc.MethodDescriptor.<es.bsc.dataclay.proto.metadata.CloseSessionRequest, com.google.protobuf.Empty>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "CloseSession"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  es.bsc.dataclay.proto.metadata.CloseSessionRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.google.protobuf.Empty.getDefaultInstance()))
              .setSchemaDescriptor(new MetadataServiceMethodDescriptorSupplier("CloseSession"))
              .build();
        }
      }
    }
    return getCloseSessionMethod;
  }

  private static volatile io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.NewDatasetRequest,
      com.google.protobuf.Empty> getNewDatasetMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "NewDataset",
      requestType = es.bsc.dataclay.proto.metadata.NewDatasetRequest.class,
      responseType = com.google.protobuf.Empty.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.NewDatasetRequest,
      com.google.protobuf.Empty> getNewDatasetMethod() {
    io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.NewDatasetRequest, com.google.protobuf.Empty> getNewDatasetMethod;
    if ((getNewDatasetMethod = MetadataServiceGrpc.getNewDatasetMethod) == null) {
      synchronized (MetadataServiceGrpc.class) {
        if ((getNewDatasetMethod = MetadataServiceGrpc.getNewDatasetMethod) == null) {
          MetadataServiceGrpc.getNewDatasetMethod = getNewDatasetMethod =
              io.grpc.MethodDescriptor.<es.bsc.dataclay.proto.metadata.NewDatasetRequest, com.google.protobuf.Empty>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "NewDataset"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  es.bsc.dataclay.proto.metadata.NewDatasetRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.google.protobuf.Empty.getDefaultInstance()))
              .setSchemaDescriptor(new MetadataServiceMethodDescriptorSupplier("NewDataset"))
              .build();
        }
      }
    }
    return getNewDatasetMethod;
  }

  private static volatile io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.GetAllBackendsRequest,
      es.bsc.dataclay.proto.metadata.GetAllBackendsResponse> getGetAllBackendsMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "GetAllBackends",
      requestType = es.bsc.dataclay.proto.metadata.GetAllBackendsRequest.class,
      responseType = es.bsc.dataclay.proto.metadata.GetAllBackendsResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.GetAllBackendsRequest,
      es.bsc.dataclay.proto.metadata.GetAllBackendsResponse> getGetAllBackendsMethod() {
    io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.GetAllBackendsRequest, es.bsc.dataclay.proto.metadata.GetAllBackendsResponse> getGetAllBackendsMethod;
    if ((getGetAllBackendsMethod = MetadataServiceGrpc.getGetAllBackendsMethod) == null) {
      synchronized (MetadataServiceGrpc.class) {
        if ((getGetAllBackendsMethod = MetadataServiceGrpc.getGetAllBackendsMethod) == null) {
          MetadataServiceGrpc.getGetAllBackendsMethod = getGetAllBackendsMethod =
              io.grpc.MethodDescriptor.<es.bsc.dataclay.proto.metadata.GetAllBackendsRequest, es.bsc.dataclay.proto.metadata.GetAllBackendsResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "GetAllBackends"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  es.bsc.dataclay.proto.metadata.GetAllBackendsRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  es.bsc.dataclay.proto.metadata.GetAllBackendsResponse.getDefaultInstance()))
              .setSchemaDescriptor(new MetadataServiceMethodDescriptorSupplier("GetAllBackends"))
              .build();
        }
      }
    }
    return getGetAllBackendsMethod;
  }

  private static volatile io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.GetDataclayRequest,
      es.bsc.dataclay.proto.common.Dataclay> getGetDataclayMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "GetDataclay",
      requestType = es.bsc.dataclay.proto.metadata.GetDataclayRequest.class,
      responseType = es.bsc.dataclay.proto.common.Dataclay.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.GetDataclayRequest,
      es.bsc.dataclay.proto.common.Dataclay> getGetDataclayMethod() {
    io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.GetDataclayRequest, es.bsc.dataclay.proto.common.Dataclay> getGetDataclayMethod;
    if ((getGetDataclayMethod = MetadataServiceGrpc.getGetDataclayMethod) == null) {
      synchronized (MetadataServiceGrpc.class) {
        if ((getGetDataclayMethod = MetadataServiceGrpc.getGetDataclayMethod) == null) {
          MetadataServiceGrpc.getGetDataclayMethod = getGetDataclayMethod =
              io.grpc.MethodDescriptor.<es.bsc.dataclay.proto.metadata.GetDataclayRequest, es.bsc.dataclay.proto.common.Dataclay>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "GetDataclay"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  es.bsc.dataclay.proto.metadata.GetDataclayRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  es.bsc.dataclay.proto.common.Dataclay.getDefaultInstance()))
              .setSchemaDescriptor(new MetadataServiceMethodDescriptorSupplier("GetDataclay"))
              .build();
        }
      }
    }
    return getGetDataclayMethod;
  }

  private static volatile io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.RegisterObjectRequest,
      com.google.protobuf.Empty> getRegisterObjectMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "RegisterObject",
      requestType = es.bsc.dataclay.proto.metadata.RegisterObjectRequest.class,
      responseType = com.google.protobuf.Empty.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.RegisterObjectRequest,
      com.google.protobuf.Empty> getRegisterObjectMethod() {
    io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.RegisterObjectRequest, com.google.protobuf.Empty> getRegisterObjectMethod;
    if ((getRegisterObjectMethod = MetadataServiceGrpc.getRegisterObjectMethod) == null) {
      synchronized (MetadataServiceGrpc.class) {
        if ((getRegisterObjectMethod = MetadataServiceGrpc.getRegisterObjectMethod) == null) {
          MetadataServiceGrpc.getRegisterObjectMethod = getRegisterObjectMethod =
              io.grpc.MethodDescriptor.<es.bsc.dataclay.proto.metadata.RegisterObjectRequest, com.google.protobuf.Empty>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "RegisterObject"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  es.bsc.dataclay.proto.metadata.RegisterObjectRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.google.protobuf.Empty.getDefaultInstance()))
              .setSchemaDescriptor(new MetadataServiceMethodDescriptorSupplier("RegisterObject"))
              .build();
        }
      }
    }
    return getRegisterObjectMethod;
  }

  private static volatile io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.GetObjectMDByIdRequest,
      es.bsc.dataclay.proto.common.ObjectMetadata> getGetObjectMDByIdMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "GetObjectMDById",
      requestType = es.bsc.dataclay.proto.metadata.GetObjectMDByIdRequest.class,
      responseType = es.bsc.dataclay.proto.common.ObjectMetadata.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.GetObjectMDByIdRequest,
      es.bsc.dataclay.proto.common.ObjectMetadata> getGetObjectMDByIdMethod() {
    io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.GetObjectMDByIdRequest, es.bsc.dataclay.proto.common.ObjectMetadata> getGetObjectMDByIdMethod;
    if ((getGetObjectMDByIdMethod = MetadataServiceGrpc.getGetObjectMDByIdMethod) == null) {
      synchronized (MetadataServiceGrpc.class) {
        if ((getGetObjectMDByIdMethod = MetadataServiceGrpc.getGetObjectMDByIdMethod) == null) {
          MetadataServiceGrpc.getGetObjectMDByIdMethod = getGetObjectMDByIdMethod =
              io.grpc.MethodDescriptor.<es.bsc.dataclay.proto.metadata.GetObjectMDByIdRequest, es.bsc.dataclay.proto.common.ObjectMetadata>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "GetObjectMDById"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  es.bsc.dataclay.proto.metadata.GetObjectMDByIdRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  es.bsc.dataclay.proto.common.ObjectMetadata.getDefaultInstance()))
              .setSchemaDescriptor(new MetadataServiceMethodDescriptorSupplier("GetObjectMDById"))
              .build();
        }
      }
    }
    return getGetObjectMDByIdMethod;
  }

  private static volatile io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.GetObjectMDByAliasRequest,
      es.bsc.dataclay.proto.common.ObjectMetadata> getGetObjectMDByAliasMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "GetObjectMDByAlias",
      requestType = es.bsc.dataclay.proto.metadata.GetObjectMDByAliasRequest.class,
      responseType = es.bsc.dataclay.proto.common.ObjectMetadata.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.GetObjectMDByAliasRequest,
      es.bsc.dataclay.proto.common.ObjectMetadata> getGetObjectMDByAliasMethod() {
    io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.GetObjectMDByAliasRequest, es.bsc.dataclay.proto.common.ObjectMetadata> getGetObjectMDByAliasMethod;
    if ((getGetObjectMDByAliasMethod = MetadataServiceGrpc.getGetObjectMDByAliasMethod) == null) {
      synchronized (MetadataServiceGrpc.class) {
        if ((getGetObjectMDByAliasMethod = MetadataServiceGrpc.getGetObjectMDByAliasMethod) == null) {
          MetadataServiceGrpc.getGetObjectMDByAliasMethod = getGetObjectMDByAliasMethod =
              io.grpc.MethodDescriptor.<es.bsc.dataclay.proto.metadata.GetObjectMDByAliasRequest, es.bsc.dataclay.proto.common.ObjectMetadata>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "GetObjectMDByAlias"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  es.bsc.dataclay.proto.metadata.GetObjectMDByAliasRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  es.bsc.dataclay.proto.common.ObjectMetadata.getDefaultInstance()))
              .setSchemaDescriptor(new MetadataServiceMethodDescriptorSupplier("GetObjectMDByAlias"))
              .build();
        }
      }
    }
    return getGetObjectMDByAliasMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.google.protobuf.Empty,
      es.bsc.dataclay.proto.metadata.GetAllObjectsResponse> getGetAllObjectsMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "GetAllObjects",
      requestType = com.google.protobuf.Empty.class,
      responseType = es.bsc.dataclay.proto.metadata.GetAllObjectsResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.google.protobuf.Empty,
      es.bsc.dataclay.proto.metadata.GetAllObjectsResponse> getGetAllObjectsMethod() {
    io.grpc.MethodDescriptor<com.google.protobuf.Empty, es.bsc.dataclay.proto.metadata.GetAllObjectsResponse> getGetAllObjectsMethod;
    if ((getGetAllObjectsMethod = MetadataServiceGrpc.getGetAllObjectsMethod) == null) {
      synchronized (MetadataServiceGrpc.class) {
        if ((getGetAllObjectsMethod = MetadataServiceGrpc.getGetAllObjectsMethod) == null) {
          MetadataServiceGrpc.getGetAllObjectsMethod = getGetAllObjectsMethod =
              io.grpc.MethodDescriptor.<com.google.protobuf.Empty, es.bsc.dataclay.proto.metadata.GetAllObjectsResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "GetAllObjects"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.google.protobuf.Empty.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  es.bsc.dataclay.proto.metadata.GetAllObjectsResponse.getDefaultInstance()))
              .setSchemaDescriptor(new MetadataServiceMethodDescriptorSupplier("GetAllObjects"))
              .build();
        }
      }
    }
    return getGetAllObjectsMethod;
  }

  private static volatile io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.DeleteAliasRequest,
      com.google.protobuf.Empty> getDeleteAliasMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "DeleteAlias",
      requestType = es.bsc.dataclay.proto.metadata.DeleteAliasRequest.class,
      responseType = com.google.protobuf.Empty.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.DeleteAliasRequest,
      com.google.protobuf.Empty> getDeleteAliasMethod() {
    io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.DeleteAliasRequest, com.google.protobuf.Empty> getDeleteAliasMethod;
    if ((getDeleteAliasMethod = MetadataServiceGrpc.getDeleteAliasMethod) == null) {
      synchronized (MetadataServiceGrpc.class) {
        if ((getDeleteAliasMethod = MetadataServiceGrpc.getDeleteAliasMethod) == null) {
          MetadataServiceGrpc.getDeleteAliasMethod = getDeleteAliasMethod =
              io.grpc.MethodDescriptor.<es.bsc.dataclay.proto.metadata.DeleteAliasRequest, com.google.protobuf.Empty>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "DeleteAlias"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  es.bsc.dataclay.proto.metadata.DeleteAliasRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.google.protobuf.Empty.getDefaultInstance()))
              .setSchemaDescriptor(new MetadataServiceMethodDescriptorSupplier("DeleteAlias"))
              .build();
        }
      }
    }
    return getDeleteAliasMethod;
  }

  private static volatile io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.NewAliasRequest,
      com.google.protobuf.Empty> getNewAliasMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "NewAlias",
      requestType = es.bsc.dataclay.proto.metadata.NewAliasRequest.class,
      responseType = com.google.protobuf.Empty.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.NewAliasRequest,
      com.google.protobuf.Empty> getNewAliasMethod() {
    io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.NewAliasRequest, com.google.protobuf.Empty> getNewAliasMethod;
    if ((getNewAliasMethod = MetadataServiceGrpc.getNewAliasMethod) == null) {
      synchronized (MetadataServiceGrpc.class) {
        if ((getNewAliasMethod = MetadataServiceGrpc.getNewAliasMethod) == null) {
          MetadataServiceGrpc.getNewAliasMethod = getNewAliasMethod =
              io.grpc.MethodDescriptor.<es.bsc.dataclay.proto.metadata.NewAliasRequest, com.google.protobuf.Empty>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "NewAlias"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  es.bsc.dataclay.proto.metadata.NewAliasRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.google.protobuf.Empty.getDefaultInstance()))
              .setSchemaDescriptor(new MetadataServiceMethodDescriptorSupplier("NewAlias"))
              .build();
        }
      }
    }
    return getNewAliasMethod;
  }

  private static volatile io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.GetAllAliasRequest,
      es.bsc.dataclay.proto.metadata.GetAllAliasResponse> getGetAllAliasMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "GetAllAlias",
      requestType = es.bsc.dataclay.proto.metadata.GetAllAliasRequest.class,
      responseType = es.bsc.dataclay.proto.metadata.GetAllAliasResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.GetAllAliasRequest,
      es.bsc.dataclay.proto.metadata.GetAllAliasResponse> getGetAllAliasMethod() {
    io.grpc.MethodDescriptor<es.bsc.dataclay.proto.metadata.GetAllAliasRequest, es.bsc.dataclay.proto.metadata.GetAllAliasResponse> getGetAllAliasMethod;
    if ((getGetAllAliasMethod = MetadataServiceGrpc.getGetAllAliasMethod) == null) {
      synchronized (MetadataServiceGrpc.class) {
        if ((getGetAllAliasMethod = MetadataServiceGrpc.getGetAllAliasMethod) == null) {
          MetadataServiceGrpc.getGetAllAliasMethod = getGetAllAliasMethod =
              io.grpc.MethodDescriptor.<es.bsc.dataclay.proto.metadata.GetAllAliasRequest, es.bsc.dataclay.proto.metadata.GetAllAliasResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "GetAllAlias"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  es.bsc.dataclay.proto.metadata.GetAllAliasRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  es.bsc.dataclay.proto.metadata.GetAllAliasResponse.getDefaultInstance()))
              .setSchemaDescriptor(new MetadataServiceMethodDescriptorSupplier("GetAllAlias"))
              .build();
        }
      }
    }
    return getGetAllAliasMethod;
  }

  /**
   * Creates a new async stub that supports all call types for the service
   */
  public static MetadataServiceStub newStub(io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<MetadataServiceStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<MetadataServiceStub>() {
        @java.lang.Override
        public MetadataServiceStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new MetadataServiceStub(channel, callOptions);
        }
      };
    return MetadataServiceStub.newStub(factory, channel);
  }

  /**
   * Creates a new blocking-style stub that supports unary and streaming output calls on the service
   */
  public static MetadataServiceBlockingStub newBlockingStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<MetadataServiceBlockingStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<MetadataServiceBlockingStub>() {
        @java.lang.Override
        public MetadataServiceBlockingStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new MetadataServiceBlockingStub(channel, callOptions);
        }
      };
    return MetadataServiceBlockingStub.newStub(factory, channel);
  }

  /**
   * Creates a new ListenableFuture-style stub that supports unary calls on the service
   */
  public static MetadataServiceFutureStub newFutureStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<MetadataServiceFutureStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<MetadataServiceFutureStub>() {
        @java.lang.Override
        public MetadataServiceFutureStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new MetadataServiceFutureStub(channel, callOptions);
        }
      };
    return MetadataServiceFutureStub.newStub(factory, channel);
  }

  /**
   */
  public interface AsyncService {

    /**
     * <pre>
     * Account Manager
     * </pre>
     */
    default void newAccount(es.bsc.dataclay.proto.metadata.NewAccountRequest request,
        io.grpc.stub.StreamObserver<com.google.protobuf.Empty> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getNewAccountMethod(), responseObserver);
    }

    /**
     */
    default void getAccount(es.bsc.dataclay.proto.metadata.GetAccountRequest request,
        io.grpc.stub.StreamObserver<es.bsc.dataclay.proto.metadata.GetAccountResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getGetAccountMethod(), responseObserver);
    }

    /**
     * <pre>
     * Session Manager
     * </pre>
     */
    default void newSession(es.bsc.dataclay.proto.metadata.NewSessionRequest request,
        io.grpc.stub.StreamObserver<es.bsc.dataclay.proto.common.Session> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getNewSessionMethod(), responseObserver);
    }

    /**
     */
    default void closeSession(es.bsc.dataclay.proto.metadata.CloseSessionRequest request,
        io.grpc.stub.StreamObserver<com.google.protobuf.Empty> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getCloseSessionMethod(), responseObserver);
    }

    /**
     * <pre>
     * Dataset Manager
     * </pre>
     */
    default void newDataset(es.bsc.dataclay.proto.metadata.NewDatasetRequest request,
        io.grpc.stub.StreamObserver<com.google.protobuf.Empty> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getNewDatasetMethod(), responseObserver);
    }

    /**
     * <pre>
     * EE-SL information
     * </pre>
     */
    default void getAllBackends(es.bsc.dataclay.proto.metadata.GetAllBackendsRequest request,
        io.grpc.stub.StreamObserver<es.bsc.dataclay.proto.metadata.GetAllBackendsResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getGetAllBackendsMethod(), responseObserver);
    }

    /**
     * <pre>
     * Federation
     * </pre>
     */
    default void getDataclay(es.bsc.dataclay.proto.metadata.GetDataclayRequest request,
        io.grpc.stub.StreamObserver<es.bsc.dataclay.proto.common.Dataclay> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getGetDataclayMethod(), responseObserver);
    }

    /**
     * <pre>
     * Object Metadata
     * </pre>
     */
    default void registerObject(es.bsc.dataclay.proto.metadata.RegisterObjectRequest request,
        io.grpc.stub.StreamObserver<com.google.protobuf.Empty> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getRegisterObjectMethod(), responseObserver);
    }

    /**
     */
    default void getObjectMDById(es.bsc.dataclay.proto.metadata.GetObjectMDByIdRequest request,
        io.grpc.stub.StreamObserver<es.bsc.dataclay.proto.common.ObjectMetadata> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getGetObjectMDByIdMethod(), responseObserver);
    }

    /**
     */
    default void getObjectMDByAlias(es.bsc.dataclay.proto.metadata.GetObjectMDByAliasRequest request,
        io.grpc.stub.StreamObserver<es.bsc.dataclay.proto.common.ObjectMetadata> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getGetObjectMDByAliasMethod(), responseObserver);
    }

    /**
     */
    default void getAllObjects(com.google.protobuf.Empty request,
        io.grpc.stub.StreamObserver<es.bsc.dataclay.proto.metadata.GetAllObjectsResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getGetAllObjectsMethod(), responseObserver);
    }

    /**
     * <pre>
     * Alias
     * </pre>
     */
    default void deleteAlias(es.bsc.dataclay.proto.metadata.DeleteAliasRequest request,
        io.grpc.stub.StreamObserver<com.google.protobuf.Empty> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getDeleteAliasMethod(), responseObserver);
    }

    /**
     */
    default void newAlias(es.bsc.dataclay.proto.metadata.NewAliasRequest request,
        io.grpc.stub.StreamObserver<com.google.protobuf.Empty> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getNewAliasMethod(), responseObserver);
    }

    /**
     */
    default void getAllAlias(es.bsc.dataclay.proto.metadata.GetAllAliasRequest request,
        io.grpc.stub.StreamObserver<es.bsc.dataclay.proto.metadata.GetAllAliasResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getGetAllAliasMethod(), responseObserver);
    }
  }

  /**
   * Base class for the server implementation of the service MetadataService.
   */
  public static abstract class MetadataServiceImplBase
      implements io.grpc.BindableService, AsyncService {

    @java.lang.Override public final io.grpc.ServerServiceDefinition bindService() {
      return MetadataServiceGrpc.bindService(this);
    }
  }

  /**
   * A stub to allow clients to do asynchronous rpc calls to service MetadataService.
   */
  public static final class MetadataServiceStub
      extends io.grpc.stub.AbstractAsyncStub<MetadataServiceStub> {
    private MetadataServiceStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected MetadataServiceStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new MetadataServiceStub(channel, callOptions);
    }

    /**
     * <pre>
     * Account Manager
     * </pre>
     */
    public void newAccount(es.bsc.dataclay.proto.metadata.NewAccountRequest request,
        io.grpc.stub.StreamObserver<com.google.protobuf.Empty> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getNewAccountMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void getAccount(es.bsc.dataclay.proto.metadata.GetAccountRequest request,
        io.grpc.stub.StreamObserver<es.bsc.dataclay.proto.metadata.GetAccountResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getGetAccountMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     * <pre>
     * Session Manager
     * </pre>
     */
    public void newSession(es.bsc.dataclay.proto.metadata.NewSessionRequest request,
        io.grpc.stub.StreamObserver<es.bsc.dataclay.proto.common.Session> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getNewSessionMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void closeSession(es.bsc.dataclay.proto.metadata.CloseSessionRequest request,
        io.grpc.stub.StreamObserver<com.google.protobuf.Empty> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getCloseSessionMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     * <pre>
     * Dataset Manager
     * </pre>
     */
    public void newDataset(es.bsc.dataclay.proto.metadata.NewDatasetRequest request,
        io.grpc.stub.StreamObserver<com.google.protobuf.Empty> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getNewDatasetMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     * <pre>
     * EE-SL information
     * </pre>
     */
    public void getAllBackends(es.bsc.dataclay.proto.metadata.GetAllBackendsRequest request,
        io.grpc.stub.StreamObserver<es.bsc.dataclay.proto.metadata.GetAllBackendsResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getGetAllBackendsMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     * <pre>
     * Federation
     * </pre>
     */
    public void getDataclay(es.bsc.dataclay.proto.metadata.GetDataclayRequest request,
        io.grpc.stub.StreamObserver<es.bsc.dataclay.proto.common.Dataclay> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getGetDataclayMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     * <pre>
     * Object Metadata
     * </pre>
     */
    public void registerObject(es.bsc.dataclay.proto.metadata.RegisterObjectRequest request,
        io.grpc.stub.StreamObserver<com.google.protobuf.Empty> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getRegisterObjectMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void getObjectMDById(es.bsc.dataclay.proto.metadata.GetObjectMDByIdRequest request,
        io.grpc.stub.StreamObserver<es.bsc.dataclay.proto.common.ObjectMetadata> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getGetObjectMDByIdMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void getObjectMDByAlias(es.bsc.dataclay.proto.metadata.GetObjectMDByAliasRequest request,
        io.grpc.stub.StreamObserver<es.bsc.dataclay.proto.common.ObjectMetadata> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getGetObjectMDByAliasMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void getAllObjects(com.google.protobuf.Empty request,
        io.grpc.stub.StreamObserver<es.bsc.dataclay.proto.metadata.GetAllObjectsResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getGetAllObjectsMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     * <pre>
     * Alias
     * </pre>
     */
    public void deleteAlias(es.bsc.dataclay.proto.metadata.DeleteAliasRequest request,
        io.grpc.stub.StreamObserver<com.google.protobuf.Empty> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getDeleteAliasMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void newAlias(es.bsc.dataclay.proto.metadata.NewAliasRequest request,
        io.grpc.stub.StreamObserver<com.google.protobuf.Empty> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getNewAliasMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void getAllAlias(es.bsc.dataclay.proto.metadata.GetAllAliasRequest request,
        io.grpc.stub.StreamObserver<es.bsc.dataclay.proto.metadata.GetAllAliasResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getGetAllAliasMethod(), getCallOptions()), request, responseObserver);
    }
  }

  /**
   * A stub to allow clients to do synchronous rpc calls to service MetadataService.
   */
  public static final class MetadataServiceBlockingStub
      extends io.grpc.stub.AbstractBlockingStub<MetadataServiceBlockingStub> {
    private MetadataServiceBlockingStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected MetadataServiceBlockingStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new MetadataServiceBlockingStub(channel, callOptions);
    }

    /**
     * <pre>
     * Account Manager
     * </pre>
     */
    public com.google.protobuf.Empty newAccount(es.bsc.dataclay.proto.metadata.NewAccountRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getNewAccountMethod(), getCallOptions(), request);
    }

    /**
     */
    public es.bsc.dataclay.proto.metadata.GetAccountResponse getAccount(es.bsc.dataclay.proto.metadata.GetAccountRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getGetAccountMethod(), getCallOptions(), request);
    }

    /**
     * <pre>
     * Session Manager
     * </pre>
     */
    public es.bsc.dataclay.proto.common.Session newSession(es.bsc.dataclay.proto.metadata.NewSessionRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getNewSessionMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.google.protobuf.Empty closeSession(es.bsc.dataclay.proto.metadata.CloseSessionRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getCloseSessionMethod(), getCallOptions(), request);
    }

    /**
     * <pre>
     * Dataset Manager
     * </pre>
     */
    public com.google.protobuf.Empty newDataset(es.bsc.dataclay.proto.metadata.NewDatasetRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getNewDatasetMethod(), getCallOptions(), request);
    }

    /**
     * <pre>
     * EE-SL information
     * </pre>
     */
    public es.bsc.dataclay.proto.metadata.GetAllBackendsResponse getAllBackends(es.bsc.dataclay.proto.metadata.GetAllBackendsRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getGetAllBackendsMethod(), getCallOptions(), request);
    }

    /**
     * <pre>
     * Federation
     * </pre>
     */
    public es.bsc.dataclay.proto.common.Dataclay getDataclay(es.bsc.dataclay.proto.metadata.GetDataclayRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getGetDataclayMethod(), getCallOptions(), request);
    }

    /**
     * <pre>
     * Object Metadata
     * </pre>
     */
    public com.google.protobuf.Empty registerObject(es.bsc.dataclay.proto.metadata.RegisterObjectRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getRegisterObjectMethod(), getCallOptions(), request);
    }

    /**
     */
    public es.bsc.dataclay.proto.common.ObjectMetadata getObjectMDById(es.bsc.dataclay.proto.metadata.GetObjectMDByIdRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getGetObjectMDByIdMethod(), getCallOptions(), request);
    }

    /**
     */
    public es.bsc.dataclay.proto.common.ObjectMetadata getObjectMDByAlias(es.bsc.dataclay.proto.metadata.GetObjectMDByAliasRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getGetObjectMDByAliasMethod(), getCallOptions(), request);
    }

    /**
     */
    public es.bsc.dataclay.proto.metadata.GetAllObjectsResponse getAllObjects(com.google.protobuf.Empty request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getGetAllObjectsMethod(), getCallOptions(), request);
    }

    /**
     * <pre>
     * Alias
     * </pre>
     */
    public com.google.protobuf.Empty deleteAlias(es.bsc.dataclay.proto.metadata.DeleteAliasRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getDeleteAliasMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.google.protobuf.Empty newAlias(es.bsc.dataclay.proto.metadata.NewAliasRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getNewAliasMethod(), getCallOptions(), request);
    }

    /**
     */
    public es.bsc.dataclay.proto.metadata.GetAllAliasResponse getAllAlias(es.bsc.dataclay.proto.metadata.GetAllAliasRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getGetAllAliasMethod(), getCallOptions(), request);
    }
  }

  /**
   * A stub to allow clients to do ListenableFuture-style rpc calls to service MetadataService.
   */
  public static final class MetadataServiceFutureStub
      extends io.grpc.stub.AbstractFutureStub<MetadataServiceFutureStub> {
    private MetadataServiceFutureStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected MetadataServiceFutureStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new MetadataServiceFutureStub(channel, callOptions);
    }

    /**
     * <pre>
     * Account Manager
     * </pre>
     */
    public com.google.common.util.concurrent.ListenableFuture<com.google.protobuf.Empty> newAccount(
        es.bsc.dataclay.proto.metadata.NewAccountRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getNewAccountMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<es.bsc.dataclay.proto.metadata.GetAccountResponse> getAccount(
        es.bsc.dataclay.proto.metadata.GetAccountRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getGetAccountMethod(), getCallOptions()), request);
    }

    /**
     * <pre>
     * Session Manager
     * </pre>
     */
    public com.google.common.util.concurrent.ListenableFuture<es.bsc.dataclay.proto.common.Session> newSession(
        es.bsc.dataclay.proto.metadata.NewSessionRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getNewSessionMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.google.protobuf.Empty> closeSession(
        es.bsc.dataclay.proto.metadata.CloseSessionRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getCloseSessionMethod(), getCallOptions()), request);
    }

    /**
     * <pre>
     * Dataset Manager
     * </pre>
     */
    public com.google.common.util.concurrent.ListenableFuture<com.google.protobuf.Empty> newDataset(
        es.bsc.dataclay.proto.metadata.NewDatasetRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getNewDatasetMethod(), getCallOptions()), request);
    }

    /**
     * <pre>
     * EE-SL information
     * </pre>
     */
    public com.google.common.util.concurrent.ListenableFuture<es.bsc.dataclay.proto.metadata.GetAllBackendsResponse> getAllBackends(
        es.bsc.dataclay.proto.metadata.GetAllBackendsRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getGetAllBackendsMethod(), getCallOptions()), request);
    }

    /**
     * <pre>
     * Federation
     * </pre>
     */
    public com.google.common.util.concurrent.ListenableFuture<es.bsc.dataclay.proto.common.Dataclay> getDataclay(
        es.bsc.dataclay.proto.metadata.GetDataclayRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getGetDataclayMethod(), getCallOptions()), request);
    }

    /**
     * <pre>
     * Object Metadata
     * </pre>
     */
    public com.google.common.util.concurrent.ListenableFuture<com.google.protobuf.Empty> registerObject(
        es.bsc.dataclay.proto.metadata.RegisterObjectRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getRegisterObjectMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<es.bsc.dataclay.proto.common.ObjectMetadata> getObjectMDById(
        es.bsc.dataclay.proto.metadata.GetObjectMDByIdRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getGetObjectMDByIdMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<es.bsc.dataclay.proto.common.ObjectMetadata> getObjectMDByAlias(
        es.bsc.dataclay.proto.metadata.GetObjectMDByAliasRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getGetObjectMDByAliasMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<es.bsc.dataclay.proto.metadata.GetAllObjectsResponse> getAllObjects(
        com.google.protobuf.Empty request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getGetAllObjectsMethod(), getCallOptions()), request);
    }

    /**
     * <pre>
     * Alias
     * </pre>
     */
    public com.google.common.util.concurrent.ListenableFuture<com.google.protobuf.Empty> deleteAlias(
        es.bsc.dataclay.proto.metadata.DeleteAliasRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getDeleteAliasMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.google.protobuf.Empty> newAlias(
        es.bsc.dataclay.proto.metadata.NewAliasRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getNewAliasMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<es.bsc.dataclay.proto.metadata.GetAllAliasResponse> getAllAlias(
        es.bsc.dataclay.proto.metadata.GetAllAliasRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getGetAllAliasMethod(), getCallOptions()), request);
    }
  }

  private static final int METHODID_NEW_ACCOUNT = 0;
  private static final int METHODID_GET_ACCOUNT = 1;
  private static final int METHODID_NEW_SESSION = 2;
  private static final int METHODID_CLOSE_SESSION = 3;
  private static final int METHODID_NEW_DATASET = 4;
  private static final int METHODID_GET_ALL_BACKENDS = 5;
  private static final int METHODID_GET_DATACLAY = 6;
  private static final int METHODID_REGISTER_OBJECT = 7;
  private static final int METHODID_GET_OBJECT_MDBY_ID = 8;
  private static final int METHODID_GET_OBJECT_MDBY_ALIAS = 9;
  private static final int METHODID_GET_ALL_OBJECTS = 10;
  private static final int METHODID_DELETE_ALIAS = 11;
  private static final int METHODID_NEW_ALIAS = 12;
  private static final int METHODID_GET_ALL_ALIAS = 13;

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
        case METHODID_NEW_ACCOUNT:
          serviceImpl.newAccount((es.bsc.dataclay.proto.metadata.NewAccountRequest) request,
              (io.grpc.stub.StreamObserver<com.google.protobuf.Empty>) responseObserver);
          break;
        case METHODID_GET_ACCOUNT:
          serviceImpl.getAccount((es.bsc.dataclay.proto.metadata.GetAccountRequest) request,
              (io.grpc.stub.StreamObserver<es.bsc.dataclay.proto.metadata.GetAccountResponse>) responseObserver);
          break;
        case METHODID_NEW_SESSION:
          serviceImpl.newSession((es.bsc.dataclay.proto.metadata.NewSessionRequest) request,
              (io.grpc.stub.StreamObserver<es.bsc.dataclay.proto.common.Session>) responseObserver);
          break;
        case METHODID_CLOSE_SESSION:
          serviceImpl.closeSession((es.bsc.dataclay.proto.metadata.CloseSessionRequest) request,
              (io.grpc.stub.StreamObserver<com.google.protobuf.Empty>) responseObserver);
          break;
        case METHODID_NEW_DATASET:
          serviceImpl.newDataset((es.bsc.dataclay.proto.metadata.NewDatasetRequest) request,
              (io.grpc.stub.StreamObserver<com.google.protobuf.Empty>) responseObserver);
          break;
        case METHODID_GET_ALL_BACKENDS:
          serviceImpl.getAllBackends((es.bsc.dataclay.proto.metadata.GetAllBackendsRequest) request,
              (io.grpc.stub.StreamObserver<es.bsc.dataclay.proto.metadata.GetAllBackendsResponse>) responseObserver);
          break;
        case METHODID_GET_DATACLAY:
          serviceImpl.getDataclay((es.bsc.dataclay.proto.metadata.GetDataclayRequest) request,
              (io.grpc.stub.StreamObserver<es.bsc.dataclay.proto.common.Dataclay>) responseObserver);
          break;
        case METHODID_REGISTER_OBJECT:
          serviceImpl.registerObject((es.bsc.dataclay.proto.metadata.RegisterObjectRequest) request,
              (io.grpc.stub.StreamObserver<com.google.protobuf.Empty>) responseObserver);
          break;
        case METHODID_GET_OBJECT_MDBY_ID:
          serviceImpl.getObjectMDById((es.bsc.dataclay.proto.metadata.GetObjectMDByIdRequest) request,
              (io.grpc.stub.StreamObserver<es.bsc.dataclay.proto.common.ObjectMetadata>) responseObserver);
          break;
        case METHODID_GET_OBJECT_MDBY_ALIAS:
          serviceImpl.getObjectMDByAlias((es.bsc.dataclay.proto.metadata.GetObjectMDByAliasRequest) request,
              (io.grpc.stub.StreamObserver<es.bsc.dataclay.proto.common.ObjectMetadata>) responseObserver);
          break;
        case METHODID_GET_ALL_OBJECTS:
          serviceImpl.getAllObjects((com.google.protobuf.Empty) request,
              (io.grpc.stub.StreamObserver<es.bsc.dataclay.proto.metadata.GetAllObjectsResponse>) responseObserver);
          break;
        case METHODID_DELETE_ALIAS:
          serviceImpl.deleteAlias((es.bsc.dataclay.proto.metadata.DeleteAliasRequest) request,
              (io.grpc.stub.StreamObserver<com.google.protobuf.Empty>) responseObserver);
          break;
        case METHODID_NEW_ALIAS:
          serviceImpl.newAlias((es.bsc.dataclay.proto.metadata.NewAliasRequest) request,
              (io.grpc.stub.StreamObserver<com.google.protobuf.Empty>) responseObserver);
          break;
        case METHODID_GET_ALL_ALIAS:
          serviceImpl.getAllAlias((es.bsc.dataclay.proto.metadata.GetAllAliasRequest) request,
              (io.grpc.stub.StreamObserver<es.bsc.dataclay.proto.metadata.GetAllAliasResponse>) responseObserver);
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
          getNewAccountMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              es.bsc.dataclay.proto.metadata.NewAccountRequest,
              com.google.protobuf.Empty>(
                service, METHODID_NEW_ACCOUNT)))
        .addMethod(
          getGetAccountMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              es.bsc.dataclay.proto.metadata.GetAccountRequest,
              es.bsc.dataclay.proto.metadata.GetAccountResponse>(
                service, METHODID_GET_ACCOUNT)))
        .addMethod(
          getNewSessionMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              es.bsc.dataclay.proto.metadata.NewSessionRequest,
              es.bsc.dataclay.proto.common.Session>(
                service, METHODID_NEW_SESSION)))
        .addMethod(
          getCloseSessionMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              es.bsc.dataclay.proto.metadata.CloseSessionRequest,
              com.google.protobuf.Empty>(
                service, METHODID_CLOSE_SESSION)))
        .addMethod(
          getNewDatasetMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              es.bsc.dataclay.proto.metadata.NewDatasetRequest,
              com.google.protobuf.Empty>(
                service, METHODID_NEW_DATASET)))
        .addMethod(
          getGetAllBackendsMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              es.bsc.dataclay.proto.metadata.GetAllBackendsRequest,
              es.bsc.dataclay.proto.metadata.GetAllBackendsResponse>(
                service, METHODID_GET_ALL_BACKENDS)))
        .addMethod(
          getGetDataclayMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              es.bsc.dataclay.proto.metadata.GetDataclayRequest,
              es.bsc.dataclay.proto.common.Dataclay>(
                service, METHODID_GET_DATACLAY)))
        .addMethod(
          getRegisterObjectMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              es.bsc.dataclay.proto.metadata.RegisterObjectRequest,
              com.google.protobuf.Empty>(
                service, METHODID_REGISTER_OBJECT)))
        .addMethod(
          getGetObjectMDByIdMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              es.bsc.dataclay.proto.metadata.GetObjectMDByIdRequest,
              es.bsc.dataclay.proto.common.ObjectMetadata>(
                service, METHODID_GET_OBJECT_MDBY_ID)))
        .addMethod(
          getGetObjectMDByAliasMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              es.bsc.dataclay.proto.metadata.GetObjectMDByAliasRequest,
              es.bsc.dataclay.proto.common.ObjectMetadata>(
                service, METHODID_GET_OBJECT_MDBY_ALIAS)))
        .addMethod(
          getGetAllObjectsMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.google.protobuf.Empty,
              es.bsc.dataclay.proto.metadata.GetAllObjectsResponse>(
                service, METHODID_GET_ALL_OBJECTS)))
        .addMethod(
          getDeleteAliasMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              es.bsc.dataclay.proto.metadata.DeleteAliasRequest,
              com.google.protobuf.Empty>(
                service, METHODID_DELETE_ALIAS)))
        .addMethod(
          getNewAliasMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              es.bsc.dataclay.proto.metadata.NewAliasRequest,
              com.google.protobuf.Empty>(
                service, METHODID_NEW_ALIAS)))
        .addMethod(
          getGetAllAliasMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              es.bsc.dataclay.proto.metadata.GetAllAliasRequest,
              es.bsc.dataclay.proto.metadata.GetAllAliasResponse>(
                service, METHODID_GET_ALL_ALIAS)))
        .build();
  }

  private static abstract class MetadataServiceBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoFileDescriptorSupplier, io.grpc.protobuf.ProtoServiceDescriptorSupplier {
    MetadataServiceBaseDescriptorSupplier() {}

    @java.lang.Override
    public com.google.protobuf.Descriptors.FileDescriptor getFileDescriptor() {
      return es.bsc.dataclay.proto.metadata.Metadata.getDescriptor();
    }

    @java.lang.Override
    public com.google.protobuf.Descriptors.ServiceDescriptor getServiceDescriptor() {
      return getFileDescriptor().findServiceByName("MetadataService");
    }
  }

  private static final class MetadataServiceFileDescriptorSupplier
      extends MetadataServiceBaseDescriptorSupplier {
    MetadataServiceFileDescriptorSupplier() {}
  }

  private static final class MetadataServiceMethodDescriptorSupplier
      extends MetadataServiceBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoMethodDescriptorSupplier {
    private final String methodName;

    MetadataServiceMethodDescriptorSupplier(String methodName) {
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
      synchronized (MetadataServiceGrpc.class) {
        result = serviceDescriptor;
        if (result == null) {
          serviceDescriptor = result = io.grpc.ServiceDescriptor.newBuilder(SERVICE_NAME)
              .setSchemaDescriptor(new MetadataServiceFileDescriptorSupplier())
              .addMethod(getNewAccountMethod())
              .addMethod(getGetAccountMethod())
              .addMethod(getNewSessionMethod())
              .addMethod(getCloseSessionMethod())
              .addMethod(getNewDatasetMethod())
              .addMethod(getGetAllBackendsMethod())
              .addMethod(getGetDataclayMethod())
              .addMethod(getRegisterObjectMethod())
              .addMethod(getGetObjectMDByIdMethod())
              .addMethod(getGetObjectMDByAliasMethod())
              .addMethod(getGetAllObjectsMethod())
              .addMethod(getDeleteAliasMethod())
              .addMethod(getNewAliasMethod())
              .addMethod(getGetAllAliasMethod())
              .build();
        }
      }
    }
    return result;
  }
}
