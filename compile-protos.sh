
# For python
python3 -m grpc_tools.protoc \
--proto_path=dataclay-common \
--python_out=src/dataclay \
dataclay-common/protos/common_messages.proto \
dataclay-common/protos/dataservice_messages.proto \
dataclay-common/protos/logicmodule_messages.proto

# Protobuf + grpc
python3 -m grpc_tools.protoc \
--proto_path=dataclay-common \
--python_out=src/dataclay \
--grpc_python_out=src/dataclay \
dataclay-common/protos/dataservice.proto \
dataclay-common/protos/logicmodule.proto \
dataclay-common/protos/metadata_service.proto

# Replace wrong import from pb2_grpc.py
sed -i 's/from protos/from ./g' \
src/dataclay/protos/*pb2*.py