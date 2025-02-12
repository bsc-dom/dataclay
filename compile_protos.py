#!/usr/bin/env python3

import inspect
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


def run_protoc():
    # Here because during the build process, CustomBuildHook will be imported
    # *before* knowing the dependencies of the hook itself.
    import grpc_tools.protoc

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


def find_config_settings_in_hatchling() -> dict[str, Any]:
    # Terrible workaround (their words, not mine) given by @virtuald
    # https://github.com/pypa/hatch/issues/1072#issuecomment-2448985229
    # Hopefully this will be fixed in the future
    for frame_info in inspect.stack():
        frame = frame_info.frame
        module = inspect.getmodule(frame)
        if (
            module
            and module.__name__.startswith("hatchling.build")
            and "config_settings" in frame.f_locals
        ):
            return frame.f_locals["config_settings"]

    return {}


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        run_protoc()

    def dependencies(self):
        if find_config_settings_in_hatchling().get("LEGACY_DEPS", "False").lower() in (
            "true",
            "on",
            "1",
            "y",
            "yes",
        ):
            return ["grpcio-tools==1.48.2"]
        else:
            return ["grpcio-tools==1.67.1"]


if __name__ == "__main__":
    run_protoc()
