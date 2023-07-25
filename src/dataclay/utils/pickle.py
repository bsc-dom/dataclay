import io
import logging
import pickle
from uuid import UUID

from dataclay.dataclay_object import DataClayObject
from dataclay.runtime import get_runtime

logger = logging.getLogger(__name__)


class RecursiveLocalPickler(pickle.Pickler):
    def __init__(
        self,
        file,
        visited_local_objects: dict[UUID, DataClayObject],
        # visited_remote_objects: dict[UUID, DataClayObject],
        serialized: list[bytes],
    ):
        super().__init__(file)
        self.visited_local_objects = visited_local_objects
        # self.visited_remote_objects = visited_remote_objects
        self.serialized = serialized

    def persistent_id(self, obj):
        if isinstance(obj, DataClayObject):
            if obj._dc_is_local:
                if obj._dc_id not in self.visited_local_objects:
                    self.visited_local_objects[obj._dc_id] = obj
                    f = io.BytesIO()
                    if not obj._dc_is_loaded:
                        get_runtime().load_object_from_db(obj)
                    RecursiveLocalPickler(f, self.visited_local_objects, self.serialized).dump(
                        obj._dc_dict
                    )
                    self.serialized.append(f.getvalue())

                return ("local", obj._dc_id, obj.__class__)
            else:
                # Adding to visited_remote_objects
                # if obj._dc_id not in self.visited_local_objects:
                #     self.visited_local_objects[obj._dc_id] = obj
                return ("remote", obj._dc_id, obj.__class__)
        else:
            return None


class RecursiveLocalUnpickler(pickle.Unpickler):
    def __init__(self, file, unserialized: dict[UUID, DataClayObject]):
        super().__init__(file)
        self.unserialized = unserialized

    def persistent_load(self, pers_id):
        tag, object_id, cls = pers_id
        if tag == "remote":
            return get_runtime().get_object_by_id(object_id)
        elif tag == "local":
            try:
                return self.unserialized[object_id]
            except KeyError:
                proxy_object = cls.new_proxy_object()
                self.unserialized[object_id] = proxy_object
                return proxy_object

        raise pickle.UnpicklingError("unsupported persistent object")


class RecursiveLocalPicklerV2(pickle.Pickler):
    """This should be used only in backends, where all objects are for sure registered
    This won't serialize local objects which are replicas and will consider them as remotes"""

    def __init__(
        self,
        file,
        visited_local_objects: dict[UUID, DataClayObject],
        visited_remote_objects: dict[UUID, DataClayObject],
        serialized: list[bytes],
    ):
        super().__init__(file)
        self.visited_local_objects = visited_local_objects
        self.visited_remote_objects = visited_remote_objects
        self.serialized = serialized

    def persistent_id(self, obj):
        if isinstance(obj, DataClayObject):
            if obj._dc_is_local and not obj._dc_is_replica:
                if obj._dc_id not in self.visited_local_objects:
                    self.visited_local_objects[obj._dc_id] = obj

                    f = io.BytesIO()
                    if not obj._dc_is_loaded:
                        get_runtime().load_object_from_db(obj)
                    RecursiveLocalPicklerV2(
                        f, self.visited_local_objects, self.visited_remote_objects, self.serialized
                    ).dump(obj._dc_dict)
                    self.serialized.append(f.getvalue())

            else:
                # Adding to visited_remote_objects
                if obj._dc_id not in self.visited_remote_objects:
                    self.visited_remote_objects[obj._dc_id] = obj

        # return None


def recursive_local_pickler(instance, visited_local_objects=None, visited_remote_objects=None):
    f = io.BytesIO()
    serialized_local_dicts = []

    if visited_local_objects is None:
        visited_local_objects = {}
    if visited_remote_objects is None:
        visited_remote_objects = {}

    visited_local_objects[instance._dc_id] = instance

    RecursiveLocalPicklerV2(
        f, visited_local_objects, visited_remote_objects, serialized_local_dicts
    ).dump(instance._dc_dict)

    serialized_local_dicts.append(f.getvalue())

    return serialized_local_dicts
