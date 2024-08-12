""" Class description goes here. """

import asyncio
import logging
import os
from typing import Any

from dotenv import dotenv_values

# "Publish" the StorageObject (which is a plain DataClayObject internally)
from dataclay import DataClayObject as StorageObject
from dataclay.client.api import Client

# Also "publish" the split method
# from dataclay.contrib.splitting import split
from dataclay.config import exec_constraints_var, get_runtime
from dataclay.event_loop import get_dc_event_loop
from dataclay.metadata.kvdata import ObjectMetadata

# The StorageDict and StorageList data structures
# from .models.storagedict import StorageDict
# from .models.storagelist import StorageList

_initialized = False

logger = logging.getLogger("dataclay.storage.api")

_client: Client = None


def get_client() -> Client:
    """Get the global (singleton) Client instance.

    This can be run in the worker nodes (i.e., inside a task). Given the
    regular initialization flow of the worker (i.e., after it calls initWorker)
    a global Client instane is available and can be used.
    """
    return _client


def getByID(object_md_json: str):
    """Get a Persistent Object from its JSON-encoded metadata.

    Args:
        object_md_json: JSON-encoded string of an object metadata

    Returns:
        The DataClayObject identified by the given object_md_json
    """
    loop = get_dc_event_loop()
    object_md = ObjectMetadata.model_validate_json(object_md_json)
    return asyncio.run_coroutine_threadsafe(
        get_runtime().get_object_by_id(object_md.id, object_md), loop
    ).result()


def initWorker(config_file_path, **kwargs):
    """Worker-side initialization.

    CURRENT BEHAVIOUR IMPORTANT CONSIDERATIONS

    This initialization is **not** a complete one, this performs a
    `per_network_init`ialization. This is done because it is assumed that
    COMPSs will proceed to fork the process and then call the
    `initWorkerPostFort`.

    Be sure to leave all the process fragile stuff in the other call. But keep
    in mind that calling to initWorkerPostFor is not optional --after this init
    the library is not in a consistent state.

    :param config_file_path: Path to storage.properties configuration file.
    :param kwargs: Additional arguments, currently unused. For future use
      and/or other Persistent Object Library requirements.
    """
    logger.info("Initialization of worker through storage.api")

    env_vars = dotenv_values(config_file_path)
    os.environ.update(env_vars)

    global _client
    _client = Client()


def initWorkerPostFork():
    """Worker-side initialization after forking the process.

    CURRENT BEHAVIOUR IMPORTANT CONSIDERATIONS

    This initialization must be done after the `initWorker` and all the
    libraries that are "fork-fragile" must be addressed here.

    To this date, only gRPC client is initialized here because they are not
    process-safe.

    Once this method is called, dataClay can be considered "initialized".
    """
    logger.warning("Finishing initialization (post-fork)")
    _client.start()


def finishWorkerPostFork():
    """Worker-side finalization per forked process.

    This finalization must be done before the finishWorker. This must be
    called once per forked process, and must match the calls of
    initWorkerPostFork.

    That means that each call to initWorkerPostFork must have its "related"
    (i.e. called from the same process) call to finishWorkerPostFork.
    """
    logger.warning("Finishing dataClay (post-fork)")
    _client.stop()
    logger.debug("Finalization post-fork finished")


def init(config_file_path, **kwargs):
    """Master-side initialization.

    Identical to initWorker (right now, may change).
    """
    logger.info("Initialization of storage.api")
    initWorker(config_file_path)
    initWorkerPostFork()


def finishWorker(**kwargs):
    """Worker-side finalization.

    :param kwargs: Additional arguments, currently unused. For future use
      and/or other Persistent Object Library requirements.
    """
    logger.info("Finalization of worker through storage.api")
    # Nothing to do here, because finishWorkerPostFork is the real hero here
    pass


def finish(**kwargs):
    """Master-side initialization.

    Identical to finishworker (right now, may change).
    """
    logger.info("Finalization of storage.api")
    _client.stop()


class TaskContext(object):
    def __init__(self, logger, values, config_file_path=None, **kwargs):
        """Initialize the TaskContext for the current task.
        :param logger: A logger that can be used for the storage.api
        :param values: The values of the Task (unused right now)
        :param config_file_path: DEPRECATED. Was required by dataClay.
        Has been moved to initWorker.
        :param kwargs: Additional arguments, currently unused. For future use
        and/or other Persistent Object Library requirements.

        A task is about to be executed and this ContextManager encloses its
        execution. This context is used by the COMPSs Worker.
        """
        self.logger = logger
        self.values = values

    def __enter__(self):
        """Perform initialization (ContextManager starts)"""
        self.logger.info("Starting task")
        logger.info("Starting task")

    def __exit__(self, etype, value, tb):
        """Perform finalization (ContextManager ends)"""
        # ... manage exception if desired
        if etype is not None:
            self.logger.warn("Exception received: %s", etype)
            logger.warn("Exception received: %s", etype)

            import traceback

            traceback.print_exception(etype, value, tb)

            pass  # Exception occurred
            # Return true if you want to suppress the exception

        # Finished
        self.logger.info("Ending task")
        logger.info("Ending task")


class ConstraintsContext:
    """Context manager to set constraints for a block of code of active methods.

    The available constraints are:
    - max_threads (int): Maximum number of threads that can be used in parallel. Defaults to None (unlimited).
    """

    def __init__(self, new_config: dict[str, Any]):
        self.new_config = new_config
        self.token = None
        self.old_config = None

    def __enter__(self):
        self.old_config = exec_constraints_var.get().copy()
        updated_config = self.old_config.copy()
        updated_config.update(self.new_config)
        self.token = exec_constraints_var.set(updated_config)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        exec_constraints_var.reset(self.token)


if os.getenv("DEACTIVATE_STORAGE_LIBRARY", "false").lower() == "true":
    from dataclay.contrib.dataclay_dummy import deactivate_storage_library

    deactivate_storage_library()
