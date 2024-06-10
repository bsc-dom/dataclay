import importlib
import re

from dataclay.utils.telemetry import LoggerEvent
from dataclay.virtual_dco import VirtualDataClayObject

VIRTUALDCO_BASE_CLASS = re.compile(r"VirtualDataClayObject\[([a-zA-Z0-9_.]+)\]")


def _import_class(full_class_name: str):
    module_name, class_name = full_class_name.rsplit(".", 1)
    m = importlib.import_module(module_name)
    return getattr(m, class_name)

def get_class_by_name(module_class_name: str):
    res = re.match(VIRTUALDCO_BASE_CLASS, module_class_name)
    if res:
        module_class_name = res.group(1)
        klass = _import_class(module_class_name)
        return VirtualDataClayObject._create_class_proxy(klass)
    else:
        return _import_class(module_class_name)
