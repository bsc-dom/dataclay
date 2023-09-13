import io
import logging
import pickle
from uuid import UUID

from dataclay import utils
from dataclay.dataclay_object import DataClayObject
from dataclay.runtime import get_runtime

logger = logging.getLogger(__name__)


class DataClayPickler(pickle.Pickler):
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
        if isinstance(obj, DataClayObject):
            if obj._dc_is_local and not obj._dc_is_replica:
                if obj._dc_meta.id not in self.visited_local_objects:
                    self.visited_local_objects[obj._dc_meta.id] = obj
                    if not obj._dc_is_loaded:
                        get_runtime().load_object_from_db(obj)

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
                # Adding to visited_remote_objects
                if obj._dc_meta.id not in self.visited_remote_objects:
                    self.visited_remote_objects[obj._dc_meta.id] = obj


def recursive_dcdumps(
    instance: DataClayObject,
    local_objects: dict[UUID, DataClayObject] | None = None,
    remote_objects: dict[UUID, DataClayObject] | None = None,
    make_persistent: bool = False,
):
    # Initialize local_objects and remote_objects
    serialized_local_objects = []
    if local_objects is None:
        local_objects = {}
    if remote_objects is None:
        remote_objects = {}
    local_objects[instance._dc_meta.id] = instance

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


def recursive_dcloads(object_binary, unserialized_objects: dict[UUID, DataClayObject] = None):
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


def dcdumps(obj):
    f = io.BytesIO()
    DataClayPickler(f).dump(obj)
    return f.getvalue()
