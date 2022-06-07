#!/bin/bash

# From dataclay-common
# PATH_PROTOS=dataclay-common/protos
PATH_PROTOS=../dataclay-common/protos
PATH_OUTPUT=src/dataclay/protos

python3 -m grpc_tools.protoc -I$PATH_PROTOS \
--python_out=$PATH_OUTPUT \
--grpc_python_out=$PATH_OUTPUT \
$PATH_PROTOS/*.proto &&

# # Replace import path
sed -i '0,/metadata_service_pb2/{s/metadata_service_pb2/dataclay.protos.metadata_service_pb2/}' $PATH_OUTPUT/metadata_service_pb2_grpc.py
