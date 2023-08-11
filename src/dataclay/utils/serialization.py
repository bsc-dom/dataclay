import io
import logging
import pickle
from uuid import UUID

from dataclay.dataclay_object import DataClayObject
from dataclay.runtime import get_runtime

logger = logging.getLogger(__name__)


class RecursiveDataClayObjectPickler(pickle.Pickler):
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
        if isinstance(obj, DataClayObject):
            if obj._dc_is_local and not obj._dc_is_replica:
                if obj._dc_meta.id not in self.visited_local_objects:
                    self.visited_local_objects[obj._dc_meta.id] = obj

                    f = io.BytesIO()
                    if not obj._dc_is_loaded:
                        get_runtime().load_object_from_db(obj)
                    RecursiveDataClayObjectPickler(
                        f,
                        self.visited_local_objects,
                        self.visited_remote_objects,
                        self.serialized,
                        self.make_persistent,
                    ).dump(obj._dc_dict)
                    self.serialized.append(f.getvalue())
                if self.make_persistent:
                    return ("unregistered", obj._dc_meta.id, obj.__class__)
            else:
                # Adding to visited_remote_objects
                if obj._dc_meta.id not in self.visited_remote_objects:
                    self.visited_remote_objects[obj._dc_meta.id] = obj


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


def unserialize_dataclay_object(
    dict_binary, unserialized_objects: dict[UUID, DataClayObject] = None
):
    if unserialized_objects is None:
        unserialized_objects = {}
    object_dict = RecursiveDataClayObjectUnpickler(
        io.BytesIO(dict_binary), unserialized_objects
    ).load()
    return object_dict


def serialize_dataclay_object(
    instance: DataClayObject,
    local_objects: dict[UUID, DataClayObject] | None = None,
    remote_objects: dict[UUID, DataClayObject] | None = None,
    make_persistent: bool = False,
):
    f = io.BytesIO()
    serialized_local_dicts = []

    if local_objects is None:
        local_objects = {}
    if remote_objects is None:
        remote_objects = {}

    local_objects[instance._dc_meta.id] = instance

    RecursiveDataClayObjectPickler(
        f, local_objects, remote_objects, serialized_local_dicts, make_persistent
    ).dump(instance._dc_dict)

    serialized_local_dicts.append(f.getvalue())
    return serialized_local_dicts
