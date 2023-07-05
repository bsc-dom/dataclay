import importlib

from dataclay.utils.telemetry import LoggerEvent


def get_class_by_name(module_class_name: str):
    module_name, class_name = module_class_name.rsplit(".", 1)
    m = importlib.import_module(module_name)
    return getattr(m, class_name)
