import asyncio
import contextvars
import io
import logging
import pickle
from typing import Optional
from uuid import UUID

from dataclay import utils
from dataclay.dataclay_object import DataClayObject
from dataclay.runtime import get_dc_running_loop, get_runtime
from dataclay.utils.contextvars import run_in_context

logger = logging.getLogger(__name__)


class DataClayPickler(pickle.Pickler):
    def __init__(self, file, pending_make_persistent: Optional[list[DataClayObject]] = None):
        super().__init__(file)
        self.pending_make_persistent = pending_make_persistent

    def reducer_override(self, obj):
        if isinstance(obj, DataClayObject):
            if not obj._dc_is_registered:
                # Option 0 (no async)
                # obj.make_persistent()

                # Option 1 - run_in_executor
                loop = get_dc_running_loop()
                t = asyncio.run_coroutine_threadsafe(obj.make_persistent(), loop)
                t.result()

                # Option 2 - post make_persistent
                # if self.pending_make_persistent is None:
                #     self.pending_make_persistent = []
                # if obj not in self.pending_make_persistent:
                #     self.pending_make_persistent.append(obj)
            return obj.get_by_id_sync, (obj._dc_meta.id,)
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
        This method is called to get the persistent id of an object.
        If the object is a non registered DataClayObject, then it returns a tuple with the following elements:
        - "unregistered" tag
        - object id
        - object class

        If the object is a persistent DataClayObject, then it returns None. And the reducer_override method is called.
        The reducer_override will serialize the object as a tuple with the following elements:
        - get_by_id_sync method
        - object id

        If the object is not a DataClayObject, then it returns None.
        """
        if isinstance(obj, DataClayObject):
            if obj._dc_is_local and not obj._dc_is_replica:
                if obj._dc_meta.id not in self.visited_local_objects:
                    self.visited_local_objects[obj._dc_meta.id] = obj
                    if not obj._dc_is_loaded:
                        get_runtime().data_manager.load_object(obj)

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

    # TODO: Use an executor to all pickle.dump (to release GIL?)
    # Serialize the object state (__dict__ or __getstate__), and its referees
    f = io.BytesIO()
    RecursiveDataClayPickler(
        f, local_objects, remote_objects, serialized_local_objects, make_persistent
    ).dump(instance._dc_state)

    serialized_local_objects.append(f.getvalue())
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

    object_dict, state = RecursiveDataClayObjectUnpickler(
        io.BytesIO(object_binary), unserialized_objects
    ).load()

    object_id = object_dict["_dc_meta"].id
    try:
        # In case it was already unserialized by a reference
        proxy_object = unserialized_objects[object_id]
    except KeyError:
        cls: type[DataClayObject] = utils.get_class_by_name(object_dict["_dc_meta"].class_name)
        proxy_object = cls.new_proxy_object()
        unserialized_objects[object_id] = proxy_object

    vars(proxy_object).update(object_dict)
    if state:
        proxy_object.__setstate__(state)
    return proxy_object


async def dcdumps(obj):
    logger.debug("Serializing object in executor")

    # TODO: avoid calling run_in_executor if not needed. Dunnot how, but optimize!
    # If object is None, return None

    # Option 1 - run_in_executor
    loop = asyncio.get_running_loop()
    f = io.BytesIO()
    await loop.run_in_executor(
        None, run_in_context, contextvars.copy_context(), DataClayPickler(f).dump, obj
    )
    return f.getvalue()

    # Option 2 - post make_persistent
    # pending_make_persistent: list[DataClayObject] = []
    # DataClayPickler(f, pending_make_persistent=pending_make_persistent).dump(obj)
    # logger.warning(f"++++++ pending_make_persistent: {pending_make_persistent}")
    # for obj in pending_make_persistent:
    #     await obj.make_persistent()
    # return f.getvalue()


async def dcloads(binary):
    logger.debug("Deserializing binary in executor")
    # TODO: Be sure contextvars won't be need. If so, use run_in_context
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, pickle.loads, binary)
    return result
