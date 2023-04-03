"""Management of Python Classes.

This module is responsible of management of the Class Objects. A central Python
Metaclass is responsible of Class (not object) instantiation.

Note that this managers also includes most serialization/deserialization code
related to classes and function call parameters.
"""

from __future__ import annotations

import functools
import logging
import threading
import traceback
import uuid
from collections import ChainMap
from inspect import get_annotations
from uuid import UUID

from dataclay.exceptions import *
from dataclay.metadata.kvdata import ObjectMetadata
from dataclay.protos.common_messages_pb2 import LANG_PYTHON
from dataclay.runtime import get_runtime
from dataclay.utils.tracing import trace

DC_PROPERTY_PREFIX = "_dc_property_"


tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)


class ReadWriteLock:
    """Atomic Counter lock that can only be acquired when the internal counter is zero.

    If the lock is acquired, it cannot be incremented until the lock is release.

    Use the lock with context manager:
        with counter_lock:
            ...
    """

    def __init__(self):
        self.lock = threading.Lock()
        self.cv = threading.Condition()
        self.counter = 0

    def add(self, value=1):
        with self.cv:
            self.cv.wait_for(lambda: not self.lock.locked())
            self.counter += value

    def sub(self, value=1):
        with self.cv:
            self.counter -= value
            self.cv.notify_all()

    def acquire(self, timeout=None):
        with self.cv:
            # NOTE: Timeout to avoid dead lock when activemethod call flush_all
            if self.cv.wait_for(lambda: self.counter == 0, timeout):
                return self.lock.acquire(blocking=False)
            else:
                return False

    def release(self):
        with self.cv:
            self.lock.release()
            self.cv.notify_all()


def activemethod(func):
    """Decorator for DataClayObject active methods"""

    @functools.wraps(func)
    def wrapper_activemethod(self: DataClayObject, *args, **kwargs):
        logger.debug(f"Calling activemethod {func.__name__} on {self._dc_id}")
        try:
            # If the object is local executes the method locally,
            # else, executes the method in the backend
            if self._dc_is_local:
                # TODO: Use active_counter only if inside backend
                self._xdc_active_counter.add()
                result = func(self, *args, **kwargs)
                self._xdc_active_counter.sub()
                return result
            else:
                return get_runtime().call_active_method(self, func.__name__, args, kwargs)
        except Exception:
            traceback.print_exc()
            raise

    # wrapper_activemethod.is_activemethod = True
    return wrapper_activemethod


class DataClayProperty:
    __slots__ = "property_name", "dc_property_name"

    def __init__(self, property_name):
        self.property_name = property_name
        self.dc_property_name = DC_PROPERTY_PREFIX + property_name

    def __get__(self, instance: DataClayObject, owner):
        """
        | is_local | is_load |
        | True     | True    |  B (heap) or C (not persistent)
        | True     | False   |  B (stored)
        | False    | True    |  -
        | False    | False   |  B (remote) or C (persistent)
        """
        logger.debug(
            f"Calling getter for property {instance.__class__.__name__}.{self.property_name} on {instance._dc_id}"
        )

        if instance._dc_is_local:
            try:
                if not instance._dc_is_loaded:
                    get_runtime().load_object_from_db(instance)

                return getattr(instance, self.dc_property_name)
            except AttributeError as e:
                e.args = (e.args[0].replace(self.dc_property_name, self.property_name),)
                raise e
        else:
            return get_runtime().call_active_method(
                instance, "__getattribute__", (self.property_name,), {}
            )

    def __set__(self, instance: DataClayObject, value):
        """Setter for the dataClay property

        See the __get__ method for the basic behavioural explanation.
        """
        logger.debug(
            f"Calling setter for property {instance.__class__.__name__}.{self.property_name} on {instance._dc_id}"
        )

        if instance._dc_is_local:
            if not instance._dc_is_loaded:
                get_runtime().load_object_from_db(instance)

            setattr(instance, self.dc_property_name, value)
        else:
            get_runtime().call_active_method(
                instance, "__setattr__", (self.property_name, value), {}
            )


class DataClayObject:
    """Main class for Persistent Objects.

    Objects that has to be made persistent should derive this class (either
    directly, through the StorageObject alias, or through a derived class).
    """

    _dc_id: UUID
    _dc_dataset_name: str
    _dc_class: type
    _dc_class_name: str
    _dc_is_registered: bool
    _dc_backend_id: UUID
    _dc_replica_backend_ids: list[UUID]
    _dc_is_read_only: bool
    _dc_is_loaded: bool
    _dc_is_local: bool
    # _xdc_active_counter: ReadWriteLock # Commented to not break Pickle...

    def __init_subclass__(cls) -> None:
        """Defines a @property for each annotatted attribute"""
        for property_name in ChainMap(*(get_annotations(c) for c in cls.__mro__)):
            if not property_name.startswith("_dc_"):
                setattr(cls, property_name, DataClayProperty(property_name))

    def __new__(cls, *args, **kwargs):
        logger.debug(f"Creating new {cls.__name__} instance with args={args}, kwargs={kwargs}")
        obj = super().__new__(cls)
        obj.set_default_fields()
        get_runtime().add_to_heap(obj)

        if get_runtime().is_backend:
            obj.make_persistent()

        return obj

    @classmethod
    def new_proxy_object(cls, **kwargs):
        obj = super().__new__(cls)
        obj.set_default_fields()
        obj.__dict__.update(kwargs)
        return obj

    def set_default_fields(self):
        # Metadata fields
        self._dc_id = uuid.uuid4()
        self._dc_dataset_name = None
        self._dc_class_name = self.__class__.__module__ + "." + self.__class__.__name__
        self._dc_backend_id = None
        self._dc_replica_backend_ids = []
        self._dc_is_read_only = False  # Remove it?
        self._dc_is_local = True

        # Extra fields
        self._dc_class = self.__class__
        self._dc_is_registered = False  # cannot be unset (unregistered)
        self._dc_is_loaded = True
        self._xdc_active_counter = ReadWriteLock()

    @property
    def dataclay_id(self):
        """Do not use in internal code. Use _dc_id instead."""
        return self._dc_id

    @property
    def dataset(self):
        """Do not use in internal code. Use _dc_dataset_name instead."""
        return self._dc_dataset_name

    @property
    def is_registered(self):
        """_dc_is_registered"""
        return self._dc_is_registered

    @property
    def _dc_dict(self):
        """Returns __dict__ with only _dc_ attributes"""
        return {k: v for k, v in vars(self).items() if k.startswith("_dc_")}

    @property
    def _dc_properties(self):
        """Returns __dict__ with only _dc_property_ attributes"""
        return {k: v for k, v in vars(self).items() if k.startswith(DC_PROPERTY_PREFIX)}

    @property
    def metadata(self):
        return ObjectMetadata(
            self._dc_id,
            None,  # self._dc_alias,
            self._dc_dataset_name,
            self._dc_class_name,
            self._dc_backend_id,
            self._dc_replica_backend_ids,
            LANG_PYTHON,
            self._dc_is_read_only,
        )

    @metadata.setter
    def metadata(self, object_md):
        self._dc_id = object_md.id
        self._dc_dataset_name = object_md.dataset_name
        self._dc_backend_id = object_md.backend_id
        self._dc_replica_backend_ids = object_md.replica_backend_ids
        self._dc_is_read_only = object_md.is_read_only

    def clean_dc_properties(self):
        """
        Used to free up space when the client or backend lose ownership of the objects;
        or the object is being stored and unloaded
        """
        self.__dict__ = {
            k: v for k, v in vars(self).items() if not k.startswith(DC_PROPERTY_PREFIX)
        }

    ###########################
    # Object Oriented Methods #
    ###########################

    @tracer.start_as_current_span("make_persistent")
    def make_persistent(self, alias=None, backend_id=None, recursive=True):
        if alias == "":
            raise AttributeError("Alias cannot be empty")
        get_runtime().make_persistent(self, alias=alias, backend_id=backend_id, recursive=recursive)

    @classmethod
    def get_by_id(cls, object_id: UUID):
        return get_runtime().get_object_by_id(object_id)

    @classmethod
    def get_by_alias(cls, alias, dataset_name=None):
        # NOTE: "safe" was removed. The object_id cannot be obtained from alias string.
        # NOTE: The alias is unique for each dataset. dataset_name is added. If none,
        #       the default_dataset is used.
        return get_runtime().get_object_by_alias(alias, dataset_name)

    @classmethod
    def delete_alias(cls, alias, dataset_name=None):
        get_runtime().delete_alias(alias, dataset_name=dataset_name)

    def get_all_backends(self):
        """Return all the backends of this object."""
        if not self._dc_is_loaded:
            get_runtime().update_object_metadata(self)

        backends = set()
        backends.add(self._dc_backend_id)
        backends.update(self._dc_replica_backend_ids)
        return backends

    def move(self, backend_id: UUID, recursive: bool = False):
        get_runtime().move_object(self, backend_id, recursive)

    ########################
    # Object Store Methods #
    ########################

    @classmethod
    def dc_clone_by_alias(cls, alias, recursive=False):
        o = cls.get_by_alias(alias)
        return o.dc_clone(recursive)

    def dc_clone(self, recursive=False):
        """Returns a non-persistent object as a copy of the current object"""
        return get_runtime().get_copy_of_object(self, recursive)

    @classmethod
    def dc_update_by_alias(cls, alias, from_object):
        o = cls.get_by_alias(alias)
        return o.dc_update(from_object)

    def dc_update(self, from_object):
        """
        @postcondition: Updates all fields of this object with the values of the specified object
        @param from_object: instance from which values must be retrieved to set fields of current object
        """
        if from_object is None:
            return
        else:
            get_runtime().update_object(self, from_object)

    def dc_put(self, alias, backend_id=None, recursive=True):
        if not alias:
            raise AttributeError("Alias cannot be null or empty")
        get_runtime().make_persistent(self, alias=alias, backend_id=backend_id, recursive=recursive)

    # TODO: Rename it to get_id ??
    def getID(self):
        """Return the string representation of the persistent object for COMPSs.

        dataClay specific implementation: The objects are internally represented
        through ObjectID, which are UUID. In addition to that, some extra fields
        are added to the representation. Currently, a "COMPSs ID" will be:

            <objectID>:<backendID|empty>:<classID>

        In which all ID are UUID and the "hint" (backendID) can be empty.

        If the object is NOT persistent, then this method returns None.
        """
        if self._dc_is_registered:
            return "%s:%s:%s" % (
                self._dc_id,
                self._dc_backend_id,
                self._dc_class_name,
            )
        else:
            return None

    ################
    # TODO: REFACTOR
    ################

    def new_replica(self, backend_id=None, recursive=True):
        return get_runtime().new_replica(
            self._dc_id, self._dc_backend_id, backend_id, None, recursive
        )

    def new_version(self, backend_id=None, recursive=True):
        return get_runtime().new_version(
            self._dc_id,
            self._dc_backend_id,
            self._dc_class_name,
            self._dc_dataset_name,
            backend_id,
            None,
            recursive,
        )

    def consolidate_version(self):
        """Consolidate: copy contents of current version object to original object"""
        return get_runtime().consolidate_version(self._dc_id, self._dc_backend_id)

    def set_all(self, from_object):
        raise ("set_all need to be refactored")
        properties = sorted(
            self.get_class_extradata().properties.values(), key=attrgetter("position")
        )

        logger.debug("Set all properties from object %s", from_object._dc_id)

        for p in properties:
            value = getattr(from_object, p.name)
            setattr(self, p.name, value)

    #################################
    # Extradata getters and setters #
    #################################

    # DEPRECATED
    def get_original_object_id(self):
        # return self.__dclay_instance_extradata.original_object_id
        return self._dc_id

    # DEPRECATED
    def set_original_object_id(self, new_original_object_id):
        # self.__dclay_instance_extradata.original_object_id = new_original_object_id
        pass

    # DEPRECATED
    def get_root_location(self):
        # return self.__dclay_instance_extradata.root_location
        return self._dc_backend_id

    # DEPRECATED
    def set_root_location(self, new_root_location):
        # self.__dclay_instance_extradata.root_location = new_root_location
        pass

    # DEPRECATED
    def get_origin_location(self):
        # return self.__dclay_instance_extradata.origin_location
        return self._dc_backend_id

    # DEPRECATED
    def set_origin_location(self, new_origin_location):
        # self.__dclay_instance_extradata.origin_location = new_origin_location
        pass

    def add_replica_location(self, new_replica_location):
        replica_locations = self._dc_replica_backend_ids
        if replica_locations is None:
            replica_locations = list()
            self._dc_replica_backend_ids = replica_locations
        replica_locations.append(new_replica_location)

    def remove_replica_location(self, old_replica_location):
        replica_locations = self._dc_replica_backend_ids
        replica_locations.remove(old_replica_location)

    def clear_replica_locations(self):
        replica_locations = self._dc_replica_backend_ids
        if replica_locations is not None:
            replica_locations.clear()

    ##############
    # Federation #
    ##############

    def federate_to_backend(self, ext_execution_env_id, recursive=True):
        get_runtime().federate_to_backend(self, ext_execution_env_id, recursive)

    def federate(self, ext_dataclay_id, recursive=True):
        get_runtime().federate_object(self, ext_dataclay_id, recursive)

    def unfederate_from_backend(self, ext_execution_env_id, recursive=True):
        get_runtime().unfederate_from_backend(self, ext_execution_env_id, recursive)

    def unfederate(self, ext_dataclay_id=None, recursive=True):
        # FIXME: unfederate only from specific ext dataClay
        get_runtime().unfederate_object(self, ext_dataclay_id, recursive)

    def synchronize(self, field_name, value):
        # from dataclay.DataClayObjProperties import DCLAY_SETTER_PREFIX
        raise ("Synchronize need refactor")
        return get_runtime().synchronize(self, DCLAY_SETTER_PREFIX + field_name, value)

    def session_detach(self):
        """
        Detach object from session, i.e. remove reference from current session provided to current object,
            'dear garbage-collector, the current session is not using this object anymore'
        """
        get_runtime().detach_object_from_session(self._dc_id, self._dc_backend_id)

    def __reduce__(self):
        """Support for pickle protocol.

        Take into account that internal Pickle usage should be used with help
        of PersistentIdPicklerHelper and PersistentLoadPicklerHelper --for
        further information on the inner working look at the modules
        [Des|S]erializationLibUtils and both the serialize and deserialize
        methods of this class.

        This method is left here as a courtesy to end users that may need or
        want to Pickle DataClayObjects manually or through other extensions.
        """
        logger.debug("Proceeding to `__reduce__` (Pickle-related) on a DataClayObject")

        if not self._dc_is_registered:
            logger.debug("Pickling of object is causing a make_persistent")
            self.make_persistent()

        return self.get_by_id, (self._dc_id,)

    def __repr__(self):
        if self._dc_is_registered:
            return "<%s instance with ObjectID=%s>" % (
                self._dc_class_name,
                self._dc_id,
            )
        else:
            return "<%s volatile instance with ObjectID=%s>" % (
                self._dc_class_name,
                self._dc_id,
            )

    def __eq__(self, other):
        if not isinstance(other, DataClayObject):
            return False

        if not self._dc_is_registered or not other._dc_is_registered:
            return False

        return self._dc_id and other._dc_id and self._dc_id == other._dc_id

    # FIXME: Think another solution, the user may want to override the method
    def __hash__(self):
        return hash(self._dc_id)

    @activemethod
    def __setUpdate__(
        self, obj: "Any", property_name: str, value: "Any", beforeUpdate: str, afterUpdate: str
    ):
        if beforeUpdate is not None:
            getattr(self, beforeUpdate)(property_name, value)
        object.__setattr__(obj, "%s%s" % ("_dataclay_property_", property_name), value)
        if afterUpdate is not None:
            getattr(self, afterUpdate)(property_name, value)
