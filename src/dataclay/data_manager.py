from __future__ import annotations

import asyncio
import gc
import logging
import pickle
from typing import TYPE_CHECKING, Optional

import psutil

from dataclay.config import settings

from dataclay.event_loop import dc_to_thread_cpu, get_dc_event_loop
from dataclay.exceptions import DataClayException, ObjectNotFound, ObjectStorageError

from dataclay.lock_manager import lock_manager
from dataclay.utils.serialization import DataClayPickler

if TYPE_CHECKING:
    from uuid import UUID

    from dataclay.dataclay_object import DataClayObject

# logger: logging.Logger = utils.LoggerEvent(logging.getLogger(__name__))
logger = logging.getLogger(__name__)


class _DummyStoredObjects:
    def inc(self):
        """Dummy function"""
        pass

    def dec(self):
        """Dummy function"""
        pass


class DataManager:
    """This class is intended to manage all dataClay objects in runtime's memory."""

    def __init__(self):
        # Loaded objects so they cannot be GC by PythonGC.
        # It is very important to be a sorted dict (guaranteed in py3.7), so first elements
        # to arrive are cleaned before, n any deserialization from DB or parameter, objects
        # deserialized first are referrers to objects deserialized later. Second ones cannot
        # be GC if first ones are not cleaned. During GC,we should know that somehow. It's a
        # hint but improves GC a lot.
        self.loaded_objects: dict[UUID, DataClayObject] = {}
        self.memory_lock = asyncio.Lock()
        self.memory_task = None

        if settings.metrics:
            # pylint: disable=import-outside-toplevel
            from dataclay.utils import metrics

            metrics.dataclay_loaded_objects.set_function(lambda: len(self.loaded_objects))
            self.dataclay_stored_objects = metrics.dataclay_stored_objects
        else:
            self.dataclay_stored_objects = _DummyStoredObjects()

    def start_memory_monitor(self):
        if self.memory_task is None or self.memory_task.done():
            self.memory_task = get_dc_event_loop().create_task(self.memory_monitor_loop())
        else:
            logger.warning("Memory monitor is already running")

    def stop_memory_monitor(self):
        if self.memory_task:
            self.memory_task.cancel()

    async def memory_monitor_loop(self):
        try:
            while True:
                await self.check_memory()
                await asyncio.sleep(settings.memory_check_interval)
        except asyncio.CancelledError:
            logger.debug("DataManager has been cancelled.")
            raise

    async def check_memory(self):
        """Check memory usage and unload objects if necessary."""
        logger.debug("Checking memory usage")
        async with self.memory_lock:
            if self.is_memory_over_threshold():
                logger.warning("Memory is over threshold")
                logger.warning("Num loaded objects: %d", len(self.loaded_objects))

                for object_id in list(self.loaded_objects.keys()):
                    # TODO: Maybe unload multiple objects at once (with gather?)
                    # Or use a queue to unload objects, until not memory pressure
                    # NOTE: Timeout is 0, so it won't wait for the lock if in use,
                    # and will continue with the next not in use object
                    dc_object = self.loaded_objects[object_id]
                    await self.unload_object(dc_object, timeout=0, force=False)

                    # TODO: Do we need to call every time gc.collect()?
                    gc.collect()
                    if self.is_memory_below_threshold():
                        logger.info("Memory is below threshold")
                        logger.info("Num loaded objects: %d", len(self.loaded_objects))
                        break
                else:
                    logger.warning("All objects unloaded, but memory is not at ease.")
            else:
                logger.debug("Memory is below threshold")

    def add_hard_reference(self, instance: DataClayObject):
        """Add a hard reference to the provided object."""
        logger.debug("(%s) Adding hard reference to heap", instance._dc_meta.id)
        self.loaded_objects[instance._dc_meta.id] = instance

    def remove_hard_reference(self, instance: DataClayObject):
        """Remove the hard reference to the provided object."""
        logger.debug("(%s) Removing hard reference from heap", instance._dc_meta.id)
        self.loaded_objects.pop(instance._dc_meta.id, None)

    async def load_object(self, instance: DataClayObject):
        """Load the provided object from disk to memory. This method is blocking.
        Should be called from another thread to avoid blocking the main thread.

        Args:
            instance (DataClayObject): The object to load.
        """
        object_id = instance._dc_meta.id

        # BUG: Could even be necessary to make it a blocking call to avoid problems
        # (https://stackoverflow.com/questions/44358705/using-async-await-with-pickle)
        async with lock_manager.get_lock(object_id).writer_lock:
            if instance._dc_is_loaded:
                # Object may had been loaded while waiting for lock
                logger.warning("(%s) Object is already loaded", object_id)
                return
            if not instance._dc_is_local:
                # Object may had been moved to another backend while waiting for lock
                logger.warning("(%s) Object is not local", object_id)
                return

            logger.debug("(%s) Loading '%s'", object_id, instance.__class__.__name__)
            assert object_id not in self.loaded_objects

            # Load object from disk
            try:
                path = f"{settings.storage_path}/{object_id}"
                # TODO: Is it necessary dc_to_thread_cpu? Should be blocking
                # to avoid bugs with parallel loads?
                state, getstate = await dc_to_thread_cpu(pickle.load, open(path, "rb"))
                self.dataclay_stored_objects.dec()
            except Exception as e:
                raise ObjectNotFound(object_id) from e

            # Delete outdated metadata (SSOT stored in Redis)
            del state["_dc_meta"]
            vars(instance).update(state)

            # NOTE: We need to set _dc_is_loaded before calling __setstate__
            # to avoid infinite recursion
            instance._dc_is_loaded = True
            if getstate is not None:
                instance.__setstate__(getstate)

            self.add_hard_reference(instance)
            logger.debug("(%s) Loaded '%s'", object_id, instance.__class__.__name__)

    async def unload_object(
        self, instance: DataClayObject, timeout: float = 0, force: bool = False
    ):
        """Unload the provided object from memory and store it to disk.

        Args:
            instance (DataClayObject): The object to unload.
            timeout (str): The timeout to acquire the lock.
            force (bool): If True, the object will be unloaded even if the lock cannot be acquired.
        """
        object_id = instance._dc_meta.id

        # BUG: Timeout not working with aiorwlock
        # object_lock = lock_manager.get_lock(object_id)
        # if object_lock.writer_lock.locked:
        #     logger.warning("Could not acquire lock to unload object")
        #     return

        # if not force:
        #     if object_lock.writer_lock.locked:
        #         logger.warning("Could not acquire lock to unload object")
        #         return
        #     await object_lock.writer_lock.acquire()

        async with lock_manager.get_lock(object_id).writer_lock:
            if not instance._dc_is_local:
                logger.warning("(%s) Object is not local", object_id)
                return
            if not instance._dc_is_loaded:
                logger.warning("(%s) Object is not loaded", object_id)
                return

            logger.info("(%s) Unloading '%s'", object_id, instance.__class__.__name__)
            assert object_id in self.loaded_objects

            # Store object to disk
            try:
                path = f"{settings.storage_path}/{object_id}"
                DataClayPickler(open(path, "wb")).dump(instance._dc_state)
                self.dataclay_stored_objects.inc()
            except Exception as e:
                raise ObjectStorageError(object_id) from e

            # TODO: Maybe update Redis (since is loaded has changed). For access optimization.
            instance._clean_dc_properties()
            instance._dc_is_loaded = False
            self.remove_hard_reference(instance)
            logger.debug("(%s) Unloaded '%s'", object_id, instance.__class__.__name__)

    def is_memory_over_threshold(self):
        """Check if memory usage is over a specified threshold.

        Returns:
            True if memory usage exceeds the threshold, False otherwise.
        """
        return psutil.virtual_memory().percent > (settings.memory_threshold_high * 100)

    def is_memory_below_threshold(self):
        """Check if memory usage is below a specified threshold.

        Returns:
            True if memory usage is below the threshold, False otherwise.
        """
        return psutil.virtual_memory().percent < (settings.memory_threshold_low * 100)

    async def flush_all(self, unload_timeout: Optional[str] = None, force_unload: bool = True):
        """Flush all loaded objects to disk.

        Args:
            unload_timeout (Optional[str]): The timeout to acquire the lock.
            force_unload (bool): If True, the objects will be unloaded
                                 even if the lock cannot be acquired.
        """

        if unload_timeout is None:
            unload_timeout = settings.unload_timeout

        async with self.memory_lock:
            logger.debug("Starting to flush (%d) loaded objects", len(self.loaded_objects))
            for object_id in list(self.loaded_objects.keys()):
                await self.unload_object(
                    self.loaded_objects[object_id], timeout=unload_timeout, force=force_unload
                )
            logger.debug("Num loaded objects not flushed: %d", len(self.loaded_objects))
