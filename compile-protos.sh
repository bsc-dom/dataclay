
# For python
python3 -m grpc_tools.protoc \
--proto_path=dataclay-common \
--python_out=src/dataclay \
dataclay-common/proto/common.proto

# Protobuf + grpc
python3 -m grpc_tools.protoc \
--proto_path=dataclay-common \
--python_out=src/dataclay \
--grpc_python_out=src/dataclay \
dataclay-common/proto/backend.proto \
dataclay-common/proto/metadata.proto

# Replace wrong import from pb2_grpc.py
sed -i 's/from proto/from ./g' \
src/dataclay/proto/*pb2*.py