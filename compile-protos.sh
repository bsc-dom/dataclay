python3 -m grpc_tools.protoc \
--proto_path=dataclay-common \
--python_out=src \
--grpc_python_out=src \
dataclay-common/dataclay/proto/common/* \
dataclay-common/dataclay/proto/backend/* \
dataclay-common/dataclay/proto/metadata/*
