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
        visited_objects: dict[UUID, DataClayObject],
        serialized: list[bytes],
    ):
        super().__init__(file)
        self.visited_objects = visited_objects
        self.serialized = serialized

    def persistent_id(self, obj):
        if isinstance(obj, DataClayObject):
            if obj._dc_is_local:

                if obj._dc_id not in self.visited_objects:
                    self.visited_objects[obj._dc_id] = obj
                    f = io.BytesIO()
                    # TODO: If not loaded (in backend), we must load it to serialize parameters
                    RecursiveLocalPickler(f, self.visited_objects, self.serialized).dump(
                        obj._dc_dict
                    )
                    self.serialized.append(f.getvalue())

                return ("local", obj._dc_id, obj.__class__)
            else:
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
