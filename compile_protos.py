#!/usr/bin/env python3

from importlib import resources
from typing import Any
import grpc_tools.protoc

try:
    from hatchling.builders.hooks.plugin.interface import BuildHookInterface
except ModuleNotFoundError:
    if __name__ != "__main__":
        # If we are not being run interactively, then that is an error
        raise
    BuildHookInterface = object


def run_protoc():
    grpc_tools_proto = (resources.files("grpc_tools") / "_proto").resolve()
    grpc_tools.protoc.main(
        [
            "grpc_tools.protoc",
            "--proto_path=dataclay-common",
            "--python_out=src",
            "--grpc_python_out=src",
            "dataclay-common/dataclay/proto/common/common.proto",
            "dataclay-common/dataclay/proto/backend/backend.proto",
            "dataclay-common/dataclay/proto/metadata/metadata.proto",
            f"-I{grpc_tools_proto}",
        ]
    )


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        run_protoc()

    def dependencies(self):
        return ["grpcio-tools==1.48.2"]


if __name__ == "__main__":
    run_protoc()
