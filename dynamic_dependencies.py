import inspect
import os
import re
from typing import Any

from hatchling.metadata.plugin.interface import MetadataHookInterface
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

# The helper functions in this file are heavily inspired on the job layed
# out by the hatch plugin `hatch-requirements-txt`


COMMENT_RE = re.compile(r"(^|\s+)#.*$")
PIP_COMMAND_RE = re.compile(r"\s+(-[A-Za-z]|--[A-Za-z]+)")


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
            return frame.f_locals["config_settings"] or {}

    return {}


def parse_requirements(requirements: list[str]) -> tuple[list[Requirement], list[str]]:
    comments = []
    parsed_requirements: list[Requirement] = []

    for line in requirements:
        if line.lstrip().startswith("#"):
            comments.append(line)
        elif line.lstrip().startswith("-"):
            # Likely an argument to pip from a requirements.txt file intended for pip
            # (e.g. from pip-compile)
            pass
        elif line:
            # Strip comments from end of line
            line = COMMENT_RE.sub("", line)
            if "-" in line:
                line = PIP_COMMAND_RE.split(line)[0]
            req = Requirement(line)
            req.name = canonicalize_name(req.name)
            parsed_requirements.append(req)

    return parsed_requirements, comments


def load_requirements(filename: str) -> list[str]:
    if not os.path.isfile(filename):
        raise FileNotFoundError(filename)
    with open(filename, encoding="UTF-8") as fp:
        contents = fp.read()
        # Unfold lines ending with \
        contents = re.sub(r"\\\s*\n", " ", contents)
        parsed_requirements, _ = parse_requirements(contents.splitlines())
    
    return [str(r) for r in parsed_requirements]


class DynamicDependenciesMetaDataHook(MetadataHookInterface):
    def update(self, metadata):
        if find_config_settings_in_hatchling().get("LEGACY_DEPS", "False").lower() in (
            "true",
            "on",
            "1",
            "y",
            "yes",
        ):
            metadata["dependencies"] = load_requirements("requirements-legacydeps.txt")
        else:
            metadata["dependencies"] = load_requirements("requirements.txt")
