#!/bin/bash

python3 -m grpc_tools.protoc \
--proto_path=dataclay-common/protos \
--python_out=src \
--grpc_python_out=src \
$(find dataclay-common -iname "*.proto")

# List of files
# dataclay-common/protos/dataclay/communication/grpc/messages/logicmodule/logicmodule_messages.proto
# dataclay-common/protos/dataclay/communication/grpc/messages/dataservice/dataservice_messages.proto
# dataclay-common/protos/dataclay/communication/grpc/messages/common/common_messages.proto
# dataclay-common/protos/dataclay/communication/grpc/generated/dataservice/dataservice.proto
# dataclay-common/protos/dataclay/communication/grpc/generated/logicmodule/logicmodule.proto
