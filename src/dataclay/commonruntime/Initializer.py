"""Internal module used by both client and servers.

The classes and functions in the dataClay module are available (when this
makes sense) to both the dataClay client and the Python dataClay Execution
Environment.

The "client" version is available at `dataclay` package, which works as en entry
point for all the commonruntime user-friendly functions.
"""
from contextlib import contextmanager
from distutils.util import strtobool
import logging
import logging.config
import os
import yaml

__author__ = 'Alex Barcelo <alex.barcelo@bsc.es>'
__copyright__ = '2015 Barcelona Supercomputing Center (BSC-CNS)'

# Manually forcing the dataclay root logger here
logger = logging.getLogger("dataclay")
LOGGING_FORMAT = '%(asctime)s [%(processName)s] [%(threadName)s] [%(name)s] [%(levelname)s] [%(module)s:%(lineno)d] %(message)s'

###################################################################
# We like to have a little bit more of finesse wrt debug levels

# for lower-than-debug messages
TRACE_LEVEL_NUM = 5
logging.addLevelName(TRACE_LEVEL_NUM, "TRACE")

# for higher-than-debug but not printed by default
VERB_LEVEL_NUM = 15
logging.addLevelName(VERB_LEVEL_NUM, "VERBOSE")


def trace(self, message, *args, **kws):
    if self.isEnabledFor(TRACE_LEVEL_NUM):
        self._log(TRACE_LEVEL_NUM, message, args, **kws)


def verbose(self, message, *args, **kws):
    if self.isEnabledFor(VERB_LEVEL_NUM):
        self._log(VERB_LEVEL_NUM, message, args, **kws)


# And monkey patch the logging library also
logging.TRACE = TRACE_LEVEL_NUM
logging.VERB = VERB_LEVEL_NUM
logging.VERBOSE = VERB_LEVEL_NUM
logging.Logger.verb = verbose
logging.Logger.verbose = verbose
logging.Logger.trace = trace


def _get_logging_dict_config():
    """Return the dictionary config for the logging.

    This function provides either a sensible default (generated here) or loads
    a YAML file provided through the environment variable called
    "DATACLAY_LOGGING_CONFIG".
    
    :return: A dictionary that can be used with logging.dictConfig
    """
    file_config = os.getenv('DATACLAY_LOGGING_CONFIG')
    if file_config:
        dict_config = yaml.load(open(file_config, 'r'))

        handlers = dict_config.get("handlers", tuple())
        for h in handlers:
            try:
                template = handlers[h].pop("filename_template")
            except KeyError:
                pass
            else:
                new_filename = template.format(PID=os.getpid(), **os.environ)
                logger.debug("Handler %s is using `%s`, formatter from `%s`",
                             h, new_filename, template)
                # Ensure that folder exists
                try:
                    os.makedirs(os.path.dirname(new_filename))
                except OSError:
                    # If path exists, ignore
                    pass
                handlers[h]["filename"] = new_filename
        return dict_config
    else:
        debug = strtobool(os.getenv('DEBUG', "False"))
        level_name = os.getenv('LOGLEVEL')

        # Note that the priority between DEBUG and LOGLEVEL is not random, albeit arbitrary
        if level_name == "VERBOSE":
            level = logging.VERBOSE
        elif level_name == "DEBUG":
            level = logging.DEBUG
        elif level_name == "TRACE":
            level = logging.TRACE
        elif debug:
            level = logging.DEBUG
        else:
            level = logging.INFO

        return {
            "version": 1,
            "formatters": {
                "simple": {
                    "format": LOGGING_FORMAT,
                },
            },
            "handlers": {
                "dclay_console": {
                    "class": "logging.StreamHandler",
                    "level": level,
                    "formatter": "simple",
                    "stream": "ext://sys.stdout",
                }
            },
            "loggers": {
                # TODO: Add grpc logs
                "dataclay": {
                    "level": level,
                    "handlers": [
                        "dclay_console",
                    ]
                }
            }
        }


def initialize():
    """Initialize the dataClay frame (logging, tracing and constants).

    The caller should, prior to this initialize, set the ConfigOptions to valid
    values. After this initialize, the dataClay library is ready to go.
    """
    config_kwargs = _get_logging_dict_config()
    config_kwargs["disable_existing_loggers"] = False
    logging.config.dictConfig(config_kwargs)

    logger.verbose("Starting dataClay library")
    logger.verbose("Debug output seems to be enabled")

        
@contextmanager
def size_tracking(io_file):
    """Track the bytes written into a certain seekable I/O file.
    :param io_file: The I/O file being written inside the with statement.
    """
    # Hack a little bit a circular import
    from dataclay.serialization.python.lang.IntegerWrapper import IntegerWrapper

    start_track = io_file.tell()
    IntegerWrapper(32).write(io_file, 0)
    start_data = io_file.tell()
    yield
    end_data = io_file.tell()
    io_file.seek(start_track)
    IntegerWrapper(32).write(io_file, end_data - start_data)
    io_file.seek(end_data)
