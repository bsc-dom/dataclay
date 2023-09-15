""" Class description goes here. """

import logging
import os
import uuid
from distutils.util import strtobool

# "Publish" the StorageObject (which is a plain DataClayObject internally)
from dataclay import DataClayObject as StorageObject
from dataclay.client.api import Client
from dataclay.metadata.kvdata import ObjectMetadata

# Also "publish" the split method
# from dataclay.contrib.splitting import split
from dataclay.runtime import get_runtime

# The StorageDict and StorageList data structures
# from .models.storagedict import StorageDict
# from .models.storagelist import StorageList

_initialized = False

logger = logging.getLogger("dataclay.storage.api")

_client: Client = None


def getByID(object_strid):
    """Get a Persistent Object from its OID.
    :param object_strid: The string identifying object (contains both ObjectID and hint)
    :return: The (Persistent) DataClayObject
    """
    try:
        object_id, master_backend_id, class_name = object_strid.split(":")
        # NOTE: the dataset_name, replica_backend_ids, etc. won't be set to the object. It may fail!
        # possible solution: dc_obj.getID() could return the serialized ObjectMetadata with all fields.
        # Another solution would be to obtain metadata from mds, but will be slower
        object_md = ObjectMetadata(
            id=object_id, master_backend_id=master_backend_id, class_name=class_name
        )
        return get_runtime().get_object_by_id(uuid.UUID(object_id), object_md)
    except ValueError:  # this can fail for both [not enough semicolons]|[invalid uuid]
        # Fallback behaviour: no extra fields, the whole string is the ObjectID UUID
        object_id = object_strid
        return get_runtime().get_object_by_id(uuid.UUID(object_id))


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
    # parsing config_file_path

    with open(config_file_path, "r") as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key] = value

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


if strtobool(os.getenv("DEACTIVATE_STORAGE_LIBRARY", "False")):
    from dataclay.contrib.dataclay_dummy import deactivate_storage_library

    deactivate_storage_library()
