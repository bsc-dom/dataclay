from __future__ import annotations

import asyncio
import io
import logging
import pickle
import threading
from typing import Optional
from uuid import UUID

from dataclay import utils
from dataclay.config import get_runtime
from dataclay.dataclay_object import DataClayObject
from dataclay.event_loop import dc_to_thread_cpu, get_dc_event_loop

logger = logging.getLogger(__name__)


class DataClayPickler(pickle.Pickler):
    def __init__(self, file, pending_make_persistent: Optional[list[DataClayObject]] = None):
        super().__init__(file)
        self.pending_make_persistent = pending_make_persistent

    def reducer_override(self, obj):
        if isinstance(obj, DataClayObject):
            if not obj._dc_is_registered:
                obj.make_persistent()
            return obj.get_by_id, (obj._dc_meta.id,)
        else:
            return NotImplemented


class RecursiveDataClayPickler(DataClayPickler):
    def __init__(
        self,
        file,
        visited_local_objects: dict[UUID, DataClayObject],
        visited_remote_objects: dict[UUID, DataClayObject],
        serialized: list[bytes],
        make_persistent: bool,
    ):
        super().__init__(file)
        self.visited_local_objects = visited_local_objects
        self.visited_remote_objects = visited_remote_objects
        self.serialized = serialized
        self.make_persistent = make_persistent

    def persistent_id(self, obj):
        """
        Retrieves the persistent ID for an object.

        If the object is an unregistered DataClayObject, returns a tuple containing:
        - A tag "unregistered"
        - The object's ID
        - The object's class

        If the object is a registered persistent DataClayObject, returns None and triggers
        the 'reducer_override' method. This method serializes the object as a tuple with:
        - The get_by_id_sync method
        - The object's ID

        If the object is not a DataClayObject, returns None.
        """
        if isinstance(obj, DataClayObject):
            if obj._dc_is_local and not obj._dc_is_replica:
                if obj._dc_meta.id not in self.visited_local_objects:
                    self.visited_local_objects[obj._dc_meta.id] = obj
                    if not obj._dc_is_loaded:
                        # TODO: Check that assert don't create overhead
                        assert get_dc_event_loop()._thread_id != threading.get_ident()
                        asyncio.run_coroutine_threadsafe(
                            get_runtime().data_manager.load_object(obj), get_dc_event_loop()
                        ).result()

                    f = io.BytesIO()
                    RecursiveDataClayPickler(
                        f,
                        self.visited_local_objects,
                        self.visited_remote_objects,
                        self.serialized,
                        self.make_persistent,
                    ).dump(obj._dc_state)
                    self.serialized.append(f.getvalue())

                # if serializing objects for make_persistent, this are not registered
                # so they must be created we deserialization, instead of calling get_by_id
                # TODO: use obj._dc_is_registered instead of self.make_persistent
                if self.make_persistent:
                    return ("unregistered", obj._dc_meta.id, obj.__class__)
            else:
                # If the object is not local, then it is remote and just need to return the id
                # Adding object to visited_remote_objects
                if obj._dc_meta.id not in self.visited_remote_objects:
                    self.visited_remote_objects[obj._dc_meta.id] = obj


async def recursive_dcdumps(
    instance: DataClayObject,
    local_objects: Optional[dict[UUID, DataClayObject]] = None,
    remote_objects: Optional[dict[UUID, DataClayObject]] = None,
    make_persistent: bool = False,
):
    logger.debug(
        "(%s) Starting recursive_dcdumps (make_persistent=%s)",
        instance._dc_meta.id,
        make_persistent,
    )

    # Initialize local_objects and remote_objects
    serialized_local_objects = []
    if local_objects is None:
        local_objects = {}
    if remote_objects is None:
        remote_objects = {}
    local_objects[instance._dc_meta.id] = instance

    # NOTE: Executor needed to allow loading objects in parallel (async call inside non-async)
    file = io.BytesIO()
    await dc_to_thread_cpu(
        RecursiveDataClayPickler(
            file, local_objects, remote_objects, serialized_local_objects, make_persistent
        ).dump,
        instance._dc_state,
    )

    serialized_local_objects.append(file.getvalue())
    return serialized_local_objects


class RecursiveDataClayObjectUnpickler(pickle.Unpickler):
    def __init__(self, file, unserialized: dict[UUID, DataClayObject]):
        super().__init__(file)
        self.unserialized = unserialized

    def persistent_load(self, pers_id):
        tag, object_id, cls = pers_id
        if tag == "unregistered":
            try:
                return self.unserialized[object_id]
            except KeyError:
                proxy_object = cls.new_proxy_object()
                self.unserialized[object_id] = proxy_object
                return proxy_object


async def recursive_dcloads(object_binary, unserialized_objects: dict[UUID, DataClayObject] = None):
    logger.debug("Starting recursive_dcloads")

    if unserialized_objects is None:
        unserialized_objects = {}

    # Use dc_to_thread_cpu to avoid blocking the event loop in `get_by_id_sync`
    object_dict, state = await dc_to_thread_cpu(
        RecursiveDataClayObjectUnpickler(io.BytesIO(object_binary), unserialized_objects).load
    )

    object_id = object_dict["_dc_meta"].id
    try:
        # In case it was already unserialized by a reference
        proxy_object = unserialized_objects[object_id]
    except KeyError:
        cls: type[DataClayObject] = utils.get_class_by_name(object_dict["_dc_meta"].class_name)
        proxy_object = cls.new_proxy_object()
        unserialized_objects[object_id] = proxy_object

    vars(proxy_object).update(object_dict)
    if state is not None:
        proxy_object.__setstate__(state)
    return proxy_object


async def dcdumps(obj):
    """Serialize the object using DataClayPickler.
    It will manage the serialization of DataClayObjects.

    Args:
        obj: The object to serialize. Should never be a DataClayObject,
        but the _dc_state attribute of it.
    """
    logger.debug("Serializing object in executor")
    # TODO: Avoid calling dc_to_thread_cpu if not needed. Dunnot how, but optimize!
    # If object is None, return None
    # Use dc_to_thread_cpu to avoid blocking the event loop in `get_by_id_sync`
    file = io.BytesIO()
    await dc_to_thread_cpu(DataClayPickler(file).dump, obj)
    return file.getvalue()


async def dcloads(binary):
    """Deserialize the object using pickle.loads.
    It will manage the deserialization of DataClayObjects.

    Args:
        binary: The binary to deserialize. Should be the result of dcdumps.
    """
    logger.debug("Deserializing binary in executor")
    # Use dc_to_thread_cpu to avoid blocking the event loop in `get_by_id_sync`
    result = await dc_to_thread_cpu(pickle.loads, binary)
    return result
