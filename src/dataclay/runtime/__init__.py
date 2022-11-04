from dataclay.runtime.settings_hub import settings, unload_settings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dataclay.runtime.client_runtime import ClientRuntime
    from dataclay.runtime.execution_environment_runtime import ExecutionEnvironmentRuntime

current_runtime = None


def get_runtime() -> "ClientRuntime | ExecutionEnvironmentRuntime":
    return current_runtime


def set_runtime(new_runtime):
    global current_runtime
    current_runtime = new_runtime
