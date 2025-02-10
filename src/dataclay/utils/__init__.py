import importlib
import inspect
import re

from dataclay.alien import AlienDataClayObject
from dataclay.dataclay_object import DataClayProperty
from dataclay.utils.telemetry import LoggerEvent

__all__ = ["LoggerEvent"]

ALIENDCO_BASE_CLASS = re.compile(r"AlienDataClayObject\[([a-zA-Z0-9_.]+)\]")


def _import_class(full_class_name: str):
    module_name, class_name = full_class_name.rsplit(".", 1)
    m = importlib.import_module(module_name)
    return getattr(m, class_name)


def get_class_by_name(module_class_name: str):
    res = re.match(ALIENDCO_BASE_CLASS, module_class_name)
    if res:
        module_class_name = res.group(1)
        klass = _import_class(module_class_name)
        return AlienDataClayObject._create_class_proxy(klass)
    else:
        return _import_class(module_class_name)


def get_class_info(cls):
    # Retrieve all properties (DataClayProperty instances in the class's __dict__)
    properties = [name for name, attr in cls.__dict__.items() if isinstance(attr, DataClayProperty)]

    # Retrieve all activemethods (methods decorated with @activemethod in the class's __dict__)
    activemethods = [
        name
        for name, attr in cls.__dict__.items()
        if inspect.isroutine(attr) and getattr(attr, "_is_activemethod", False)
    ]

    return properties, activemethods
