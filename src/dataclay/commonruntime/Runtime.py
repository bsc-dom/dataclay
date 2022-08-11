""" Class description goes here. """

"""Common Python package.

Note that the client "entrypoint" is the package dataclay.api. Importing it
ensures proper initialization of client-side stuff.

The Execution Environment should take care of the RuntimeType and then call the
dataclay.core.initialize function.
"""
import threading
import logging

__author__ = "Alex Barcelo <alex.barcelo@bsc.es>"
__copyright__ = "2015 Barcelona Supercomputing Center (BSC-CNS)"

logger = logging.getLogger(__name__)

__all__ = ["DataClayObject", "StorageObject", "dclayMethod"]

""" Local variables in thread """
threadLocal = threading.local()

""" Cache of runtimes per thread """
runtimes_per_thread = dict()

""" Runtime for all threads in client side. It's a singleton, created once. """
client_static_runtime = None

runtime = None


def clean_runtime():
    global threadLocal
    global runtimes_per_thread
    global client_static_runtime
    threadLocal = threading.local()
    runtimes_per_thread.clear()
    client_static_runtime = None


def setRuntime(new_runtime):
    """
    @summary: set runtime in current thread. This function is used in Execution Environment
    @param runtime: runtime to set
    """
    global runtime
    runtime = new_runtime


def get_runtime():
    """
    @summary: get runtime associated to current thread. If there is no runtime, return client runtime.
    In EE if current thread has no runtime, it means thread was not prepared properly and it is wrong!
    @return runtime of the current thread
    """

    global runtime
    if runtime is None:
        from dataclay.commonruntime.ClientRuntime import ClientRuntime

        runtime = ClientRuntime()
    return runtime


# Those need the commonruntime
from dataclay.DataClayObject import (
    DataClayObject,
)  # Import after runtime to avoid circular-imports (runtime is already defined here)

StorageObject = DataClayObject  # Redundant alias
