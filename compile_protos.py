#!/usr/bin/env python3

import os.path
import tempfile
from typing import Any
from importlib import resources
from typing import Any

try:
    from hatchling.builders.hooks.plugin.interface import BuildHookInterface
except ModuleNotFoundError:
    if __name__ != "__main__":
        # If we are not being run interactively, then that is an error
        raise
    BuildHookInterface = object


def run_protoc(output_dir: str = "src") -> None:
    # Here because during the build process, CustomBuildHook will be imported
    # *before* knowing the dependencies of the hook itself.
    import grpc_tools.protoc

    grpc_tools_proto = (resources.files("grpc_tools") / "_proto").resolve()
    grpc_tools.protoc.main(
        [
            "grpc_tools.protoc",
            "--proto_path=dataclay-common",
            f"--python_out={output_dir}",
            f"--grpc_python_out={output_dir}",
            "dataclay-common/dataclay/proto/common/common.proto",
            "dataclay-common/dataclay/proto/backend/backend.proto",
            "dataclay-common/dataclay/proto/metadata/metadata.proto",
            f"-I{grpc_tools_proto}",
        ]
    )


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        self._temp_directory = tempfile.TemporaryDirectory()

        run_protoc(self._temp_directory.name)

        compiled_protos = os.path.join(self._temp_directory.name, "dataclay", "proto")
        build_data["force_include"][compiled_protos] = "dataclay/proto"

    def dependencies(self):
        return ["grpcio-tools==1.62.3"]


if __name__ == "__main__":
    run_protoc()
