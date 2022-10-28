from dataclay.runtime.settings_hub import settings, unload_settings

current_runtime = None


def get_runtime():
    return current_runtime


def set_runtime(new_runtime):
    global current_runtime
    current_runtime = new_runtime
