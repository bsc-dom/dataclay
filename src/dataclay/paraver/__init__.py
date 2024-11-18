"""Paraver related trace generation.

All the Paraver-files (.prv) generation is done through decorators and
mechanisms defined in this module. There are also capabilities for merge and
checks on the generated prv files.

Additionally, this module defines an application capable of performing several
Paraver-related routines, like "merge".
"""

from __future__ import print_function

import ctypes
import importlib
import logging
import os
import traceback
import types
from ctypes import cdll
from distutils.util import strtobool
from functools import wraps

from dataclay.config import settings
from dataclay.contrib.dummy_pycompss import task

# Explicit and manually crafted list of CLASSES to be instrumentated
CLASSES_WITH_EXTRAE_DECORATORS = {  # Similar to Java paraver/extrae AspectJ file.
    # MAPPING: package name - modules with class named equal to modulen name
    "dataclay.commonruntime": ["ClientRuntime", "DataClayRuntime", "BackendRuntime"],
    "dataclay.executionenv": ["ExecutionEnvironment"],
    "dataclay.heap": ["HeapManager"],
    "dataclay": ["DataClayObject"],
    "dataclay.serialization.lib": ["SerializationLibUtils", "DeserializationLibUtils"],
    "dataclay.serialization.python.util": ["PyTypeWildcardWrapper"],
}

PARAVER_FUNC_MAP = {}
TRACED_METHODS = []
TRACING_ENABLED = False
LOGGER = logging.getLogger(__name__)
TRACE_ENABLED = strtobool(os.getenv("PARAVER_TRACE_ENABLED", "False"))  # WARNING: not used
TASK_EVENTS = 8000010
CURRENT_AVAILABLE_TASK_ID = 0
TASK_ID = 0
PYEXTRAE = None
EXTRAE_DICT = {}
EXTRAE_CUR_PID = None
DATACLAY_EXTRAE_WRAPPER = None

# Extrae options
EXTRAE_DISABLE_ALL_OPTIONS = 0
EXTRAE_CALLER_OPTION = 1
EXTRAE_HWC_OPTION = 2
EXTRAE_MPI_HWC_OPTION = 4
EXTRAE_MPI_OPTION = 8
EXTRAE_OMP_OPTION = 16
EXTRAE_OMP_HWC_OPTION = 32
EXTRAE_UF_HWC_OPTION = 64
EXTRAE_PTHREAD_OPTION = 128
EXTRAE_PTHREAD_HWC_OPTION = 256
EXTRAE_SAMPLING_OPTION = 512
EXTRAE_ENABLE_ALL_OPTIONS = (
    EXTRAE_CALLER_OPTION
    | EXTRAE_HWC_OPTION
    | EXTRAE_MPI_HWC_OPTION
    | EXTRAE_MPI_OPTION
    | EXTRAE_OMP_OPTION
    | EXTRAE_OMP_HWC_OPTION
    | EXTRAE_UF_HWC_OPTION
    | EXTRAE_PTHREAD_OPTION
    | EXTRAE_PTHREAD_HWC_OPTION
    | EXTRAE_SAMPLING_OPTION
)


def add_function_trace(enter, prv_value):
    """
    Trace entry: Function (enter or exit).
    :param enter: Boolean to signal whether it is entering or exiting the method.
    :param prv_value: Numerical identifier for PyCOMPSs-compliant Paraver tracing.
    """

    if enter:
        LOGGER.debug("Tracing event with value %i" % (prv_value))
        PYEXTRAE.event(TASK_EVENTS, prv_value)
    else:
        PYEXTRAE.event(TASK_EVENTS, 0)


def add_network_send(
    trace_time,
    network_type,
    send_port,
    request_id,
    dest_host_ip,
    dest_host_port,
    message_size,
    method_id,
):
    """Trace a certain network send (can be a SEND_REQUEST or a SEND_RESPONSE)."""
    if not extrae_tracing_is_enabled():
        return


def add_network_receive(origin_host_ip, origin_host_port, request_id, method_id):
    """Trace a certain network receive (a RESPONSE)."""
    if not extrae_tracing_is_enabled():
        return


def initialize_extrae(initialize=False):
    """
    Initializes Extrae tracing. This function is triggered by:
        starting task id property specified in storage.conf OR
        explicit call from Execution Environment (due to a client activation)
    This function will first check if Extrae is available, if not it will raise an exception.
    Then, classes specified will be decorated.
    :param initialize: indicates if library must be initialized. False in case of compss workers.
    :type initialize: boolean
    """
    global TASK_ID
    global CURRENT_AVAILABLE_TASK_ID
    global TRACING_ENABLED
    global CLASSES_WITH_EXTRAE_DECORATORS
    global PYEXTRAE
    global EXTRAE_DICT
    global EXTRAE_CUR_PID
    LOGGER.debug(
        "Initializing Extrae with task id %i in process with pid %s " % (TASK_ID, str(os.getpid()))
    )

    # This is something very slow which should be done during initialization
    # and not during tracing.
    try:
        import pyextrae.common.extrae as pyextrae_module

        PYEXTRAE = pyextrae_module
        # PYEXTRAE.LoadExtrae(PYEXTRAE.LibrarySeq)
        LOGGER.info("Using pyextrae.common for tracing information")
    except ImportError:
        LOGGER.warning(
            "Trying to activate pyextrae but ImportError happened. Please make sure pyextrae is installed."
        )
        return

    """ Initialize synchronization events """
    if initialize:
        TASK_ID = CURRENT_AVAILABLE_TASK_ID

        TracingLibrary = "libseqtrace.so"
        LOGGER.info("Initializing Extrae")

        wrapper_lib = settings.pyclay_extrae_wrapper_lib
        if not wrapper_lib:
            wrapper_lib = os.getenv("PYCLAY_EXTRAE_WRAPPER_LIB")
            if not wrapper_lib:
                raise AttributeError(
                    "DataClay extrae wrapper cannot be found neither from session file nor any default env / path"
                )

        LOGGER.info("Using dataClay extrae wrapper at %s" % wrapper_lib)
        # set task ID
        num_tasks = TASK_ID + 1
        DATACLAY_EXTRAE_WRAPPER = cdll.LoadLibrary(wrapper_lib)
        DATACLAY_EXTRAE_WRAPPER.set_task_id(ctypes.c_uint(TASK_ID))
        DATACLAY_EXTRAE_WRAPPER.set_num_tasks(ctypes.c_uint(num_tasks))

        # init tracing
        PYEXTRAE.startTracing(TracingLibrary, False)
        EXTRAE_CUR_PID = PYEXTRAE.Extrae[os.getpid()]
        EXTRAE_CUR_PID.Extrae_init()

        CURRENT_AVAILABLE_TASK_ID = CURRENT_AVAILABLE_TASK_ID + 1  # only increment in servers
    else:
        if not os.getpid() in PYEXTRAE.Extrae:
            LOGGER.info("Cannot find Extrae for current PID.")
            EXTRAE_CUR_PID = PYEXTRAE.LoadExtrae(PYEXTRAE.LibrarySeq)
        else:
            EXTRAE_CUR_PID = PYEXTRAE.Extrae[os.getpid()]

    # initialize type and values
    load_type_values()

    """
    Apply decorators 
    Note that all non-underscore-starting methods are considered public. Take
    that in mind while programming your class. You can also explicitly avoid
    tracing a certain method by doing the following:

        def public_method_not_traced(self, ...):
            ...
        public_method_not_traced.do_not_trace = True
    """
    for module, classes in CLASSES_WITH_EXTRAE_DECORATORS.items():
        for class_name in classes:
            actual_module_name = "%s.%s" % (
                module,
                class_name,
            )  # Module name is actually the class name
            try:
                LOGGER.debug("Looking for module %s" % (actual_module_name))
                cur_module = importlib.import_module(actual_module_name)
                klass = getattr(cur_module, class_name)
                LOGGER.debug("Decorating class %r" % (klass))
                for name, obj in klass.__dict__.items():
                    if name.startswith("_"):  # ignore private methods
                        continue

                    if isinstance(
                        obj, types.FunctionType
                    ):  # @abarcelo doesn't understand why UnboundMethodType wasn't working
                        if getattr(obj, "do_not_trace", False):
                            # The user explicitly defined "do_not_trace" flag here
                            continue
                        LOGGER.debug("Decorating function %r" % (obj))
                        setattr(
                            klass, name, _trace_method_in_class(actual_module_name, class_name, obj)
                        )
            except ImportError:
                LOGGER.debug("No module %s found" % actual_module_name)
            except:
                LOGGER.debug(
                    "Exception while trying to get class %s from module %s"
                    % (class_name, actual_module_name)
                )
                traceback.print_exc()

    LOGGER.debug("Extrae is ready for task %i!" % TASK_ID)

    # Extrae is ready
    TRACING_ENABLED = True


def finish_tracing(finalize_extrae):
    """Finishing tracing.
    :param finalize_extrae: indicates extrae must be finalized (False for COMPSs doing it for us)
    :type finalize_extrae: boolean
    """
    global PYEXTRAE
    global EXTRAE_DICT
    global EXTRAE_CUR_PID
    global TRACING_ENABLED
    global TASK_ID
    global MERGER_TASK_EVENTS
    global SYNC_EVENTS
    if TRACING_ENABLED:
        LOGGER.debug("Pyextrae pids: %s" % str(PYEXTRAE.Extrae.keys()))
        LOGGER.debug("Finishing tracing with task id %i" % TASK_ID)
        try:
            define_event_types()
            if finalize_extrae:
                # EXTRAE_DICT[os.getpid()].Extrae_set_options(EXTRAE_ENABLE_ALL_OPTIONS & ~EXTRAE_PTHREAD_OPTION)
                PYEXTRAE.pyEx_trace_fini(Master=True)
                # EXTRAE_DICT[os.getpid()].Extrae_set_options(EXTRAE_DISABLE_ALL_OPTIONS)
            else:
                EXTRAE_CUR_PID.Extrae_flush()

        except:
            traceback.print_exc()
        LOGGER.debug("Finished tracing with task id %i" % TASK_ID)

        TRACING_ENABLED = False


def define_event_types():
    global TRACED_METHODS
    global EXTRAE_DICT
    global EXTRAE_CUR_PID

    nvalues = len(TRACED_METHODS) + 1
    LOGGER.debug("Defining event types. Number of traced events: %i" % nvalues)
    description = "dataClay"
    values = (ctypes.c_ulonglong * nvalues)()
    description_values = (ctypes.c_char_p * nvalues)()
    values[0] = 0
    description_values[0] = "End".encode("utf-8")
    for i in range(1, nvalues):
        try:
            description_values[i] = TRACED_METHODS[i - 1].encode("utf-8")
            values[i] = PARAVER_FUNC_MAP[description_values[i].decode("utf-8")]
            LOGGER.debug(
                "Defined event %s with value %s" % (str(description_values[i]), str(values[i]))
            )
        except KeyError:
            LOGGER.info("Tried to load untraced paraver event")

    try:
        EXTRAE_CUR_PID.Extrae_define_event_type(
            ctypes.pointer(ctypes.c_uint(TASK_EVENTS)),
            ctypes.c_char_p(description.encode("utf-8")),
            ctypes.pointer(ctypes.c_uint(nvalues)),
            ctypes.pointer(values),
            ctypes.pointer(description_values),
        )
    except KeyError:
        LOGGER.info("WARNING: Extrae define event failed")


def enable_pthreads():
    """Enables extrae pthreads"""
    PYEXTRAE.Extrae[os.getpid()].Extrae_set_options(EXTRAE_DISABLE_ALL_OPTIONS)


def disable_pthreads():
    """Disable extrae pthreads"""
    PYEXTRAE.Extrae[os.getpid()].Extrae_set_options(
        EXTRAE_ENABLE_ALL_OPTIONS & ~EXTRAE_PTHREAD_OPTION
    )


def enable_extrae_tracing():
    """Enables extrae tracing."""
    global TRACING_ENABLED
    TRACING_ENABLED = True


def get_traces():
    """At this point, pyextrae will call merger to create PRV file.
    This PRV file must be send to client/master in order to be merged with other python EE prvs and
    Java services. This function is not called for python COMPSs workers.
    :returns: prv files of current host
    :rtype: dict<string, bytes>
    """
    global TASK_EVENTS
    global PARAVER_FUNC_MAP
    global TRACED_METHODS
    traces = {}
    global TASK_ID
    set_path = settings.TRACES_DEST_PATH + "/set-0"
    LOGGER.debug("Sending files in %s" % set_path)
    for dirpath, subdirs, files in os.walk(set_path):
        for name in files:
            mpitfile = os.path.join(dirpath, name)
            LOGGER.debug("Found file %s" % name)
            in_file = open(mpitfile, "rb")  # opening for [r]eading as [b]inary
            data = in_file.read()
            in_file.close()
            traces[name] = data

    return traces


def extrae_tracing_is_enabled():
    """
    Indicates if Extrae tracing is enabled.
    :return: True if extrae tracing is enabled, false otherwise.
    :rtype: boolean
    """
    global TRACING_ENABLED
    return TRACING_ENABLED


def set_current_available_task_id(task_id):
    """
    Sets current available task id
    :param task_id: The current available task id
    :type task_id: integer
    """
    global CURRENT_AVAILABLE_TASK_ID
    CURRENT_AVAILABLE_TASK_ID = task_id


def get_current_available_task_id():
    """
    Get current available task ID
    :return: Current available task ID
    :rtype: integer
    """
    global CURRENT_AVAILABLE_TASK_ID
    return CURRENT_AVAILABLE_TASK_ID


def get_task_id():
    """
    Get  task ID
    :return: The task ID
    :rtype: integer
    """
    global TASK_ID
    return TASK_ID


def _is_network_tracing_enabled():
    """Check if network calls tracing is enabled (globally for all calls).

    :return: True if it should be traced, false otherwise.
    """
    global TRACE_ENABLED
    return TRACE_ENABLED


def _trace_method_in_class(module_name, class_name, func):
    """Decorator for methods in a class, when class is known."""
    global TRACED_METHODS
    global PARAVER_FUNC_MAP
    try:
        descriptor = "%s.%s.%s" % (module_name, class_name, func.__name__)
        LOGGER.debug("Looking for descriptor %s in paraver intercepted methods" % descriptor)
        prv_value = PARAVER_FUNC_MAP[descriptor]
        LOGGER.debug(
            "Found paraver value %r for descriptor %s in paraver intercepted methods"
            % (prv_value, descriptor)
        )
    except KeyError:
        LOGGER.warning(
            "Method `%s` (class %s, module %s) " "is not correctly registered for Paraver",
            func.__name__,
            class_name,
            module_name,
        )
        prv_value = 999

    @wraps(func)
    def func_wrapper(self, *args, **kwargs):

        if extrae_tracing_is_enabled():
            TRACED_METHODS.append(descriptor)
            add_function_trace(True, prv_value)
        # Proceed to the method call
        try:
            ret = func(self, *args, **kwargs)
        finally:
            if extrae_tracing_is_enabled():
                add_function_trace(False, prv_value)
        return ret

    return func_wrapper


def load_type_values():
    global PARAVER_FUNC_MAP

    __location__ = os.path.realpath(
        os.path.join(settings.TRACES_DEST_PATH, os.path.dirname(__file__))
    )
    prv_values_file = os.path.join(__location__, "python_paraver_values.properties")
    LOGGER.debug("Loading paraver values file from %s" % str(prv_values_file))
    with open(prv_values_file, "r") as f:
        for line in f:
            line = line.rstrip()  # removes trailing whitespace and '\n' chars
            if "=" not in line:
                continue  # skips blanks and comments w/o =
            if line.startswith("#"):
                continue  # skips comments which contain =
            k, v = line.split("=", 1)
            PARAVER_FUNC_MAP[k] = int(v)
    LOGGER.debug("Loaded %i functions to intercept" % len(PARAVER_FUNC_MAP))
