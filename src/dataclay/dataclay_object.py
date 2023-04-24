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
    """Decorator for DataClayObject active methods."""

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
        obj._set_default_fields()
        get_runtime().add_to_heap(obj)

        if get_runtime().is_backend:
            obj.make_persistent()

        return obj

    @classmethod
    def new_proxy_object(cls, **kwargs):
        obj = super().__new__(cls)
        obj._set_default_fields()
        obj.__dict__.update(kwargs)
        return obj

    def _set_default_fields(self):
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
        """ID of the object in the dataClay system."""
        return self._dc_id

    @property
    def dataset(self):
        """Name of the dataset where the object is stored."""
        return self._dc_dataset_name

    @property
    def is_registered(self):
        """Whether the object is registered in the dataClay system or not."""
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

    def _clean_dc_properties(self):
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

    def make_persistent(self, alias=None, backend_id=None, recursive=True):
        """Makes the object persistent.

        Args:
            alias: Alias of the object. If None, the object will not have an alias.
            backend_id: ID of the backend where the object will be stored. If None, the object
                will be stored in a random backend.
            recursive: If True, all objects referenced by the current one will be made persistent
                as well (in case they were not already persistent) in a recursive manner.

        Raises:
            AttributeError: If the alias is an empty string.
            RuntimeError: If the object is already persistent.
            KeyError: If the backend_id is not registered in dataClay.
        """
        if alias == "":
            raise AttributeError("Alias cannot be empty")
        get_runtime().make_persistent(self, alias=alias, backend_id=backend_id, recursive=recursive)

    @classmethod
    def get_by_id(cls, object_id: UUID):
        """Returns the object with the given id.

        Args:
            object_id: ID of the object.

        Returns:
            The object with the given id.

        Raises:
            DoesNotExistError: If the object does not exist.
        """
        return get_runtime().get_object_by_id(object_id)

    @classmethod
    def get_by_alias(cls, alias, dataset_name=None):
        """Returns the object with the given alias.

        Args:
            alias: Alias of the object.
            dataset_name: Name of the dataset where the alias is stored. If None, the session's dataset is used.

        Returns:
            The object with the given alias.

        Raises:
            DoesNotExistError: If the alias does not exist.
            DatasetIsNotAccessibleError: If the dataset is not accessible.
        """
        return get_runtime().get_object_by_alias(alias, dataset_name)

    @classmethod
    def delete_alias(cls, alias, dataset_name=None):
        """Removes the alias linked to an object.

        If this object is not referenced starting from a root object and no active session is
        accessing it, the garbage collector will remove it from the system.

        Args:
            alias: Alias to be removed.
            dataset_name: Name of the dataset where the alias is stored. If None, the session's dataset is used.

        Raises:
            DoesNotExistError: If the alias does not exist.
            DatasetIsNotAccessibleError: If the dataset is not accessible.
        """
        get_runtime().delete_alias(alias, dataset_name=dataset_name)

    def get_backends(self):
        """Returns the set of backends where the object is stored"""
        if not self._dc_is_loaded:
            get_runtime().update_object_metadata(self)

        backends = set()
        backends.add(self._dc_backend_id)
        backends.update(self._dc_replica_backend_ids)
        return backends

    def move(self, backend_id: UUID, recursive: bool = False):
        """Moves the object to the specified backend.

        Args:
            backend_id: ID of the backend where the object will be moved.
            recursive: If True, all objects referenced by this object registered in the
                same backend will also be moved.

        Raises:
            KeyError: If the backend_id is not registered in dataClay.
            ObjectNotRegisteredError: If the object is not registered in dataClay.
        """

        if not self._dc_is_registered:
            raise ObjectNotRegisteredError(self._dc_id)

        get_runtime().move_object(self, backend_id, recursive)

    ########################
    # Object Store Methods #
    ########################

    @classmethod
    def dc_clone_by_alias(cls, alias, recursive=False):
        """Returns a non-persistent object as a copy of the object with the alias specified.

        Fields referencing to other objects are kept as remote references to objects stored
        in dataClay, unless the recursive parameter is set to True.

        Args:
            alias: alias of the object to be retrieved.
            recursive:
                When this is set to True, the default behavior is altered so not only current
                object but all of its references are also retrieved locally.

        Returns:
            A new instance initialized with the field values of the object with the alias specified.

        Raises:
            DoesNotExistError: If the alias does not exist.
        """
        instance = cls.get_by_alias(alias)
        return get_runtime().get_object_copy(instance, recursive)

    def dc_clone(self, recursive=False):
        """Returns a non-persistent object as a copy of the current object.

        Args:
            recursive: When this is set to True, the default behavior is altered so not only current
                object but all of its references are also retrieved locally.

        Returns:
            A new object instance initialized with the field values of the current object.

        Raises:
            ObjectNotRegisteredError: If the object is not registered.
        """
        if not self._dc_is_registered:
            raise ObjectNotRegisteredError(self._dc_id)

        return get_runtime().get_object_copy(self, recursive)

    @classmethod
    def dc_update_by_alias(cls, alias, from_object):
        """Updates the object identified by specified alias with contents of from_object.

        Args:
            alias: alias of the object to be updated.
            from_object: object with the new values to be updated.

        Raises:
            DoesNotExistError: If the alias does not exist.
            TypeError: If the objects are not of the same type.
        """
        if cls != type(from_object):
            raise TypeError("Objects must be of the same type")

        o = cls.get_by_alias(alias)
        return o.dc_update(from_object)

    def dc_update(self, from_object):
        """Updates current object with contents of from_object.

        Args:
            from_object: object with the new values to update current object.

        Raises:
            TypeError: If the objects are not of the same type.
        """
        if type(self) != type(from_object):
            raise TypeError("Objects must be of the same type")

        get_runtime().update_object(self, from_object)

    def dc_put(self, alias, backend_id=None, recursive=True):
        """Makes the object persistent in the specified backend.

        Args:
            alias: a string that will identify the object in addition to its OID.
                Aliases are unique for dataset.
            backend_id: the backend where the object will be stored. If this parameter is not
                specified, a random backend will be chosen.
            recursive: If True, all objects referenced by the current object are also made
                persistent (in case they were not already persistent) in a recursive manner.

        Raises:
            AttributeError: if alias is null or empty.
            AlreadyExistError: If the alias already exists.
            KeyError: If the backend_id is not registered in dataClay.
            ObjectAlreadyRegisteredError: If the object is already registered in dataClay.
        """
        if not alias:
            raise AttributeError("Alias cannot be null or empty")
        get_runtime().make_persistent(self, alias=alias, backend_id=backend_id, recursive=recursive)

    # Versioning

    def new_version(self, backend_id=None, recursive=False):
        """Create a new version of the current object.

        Args:
            backend_id: the backend where the object will be stored. If this parameter is not
                specified, a random backend will be chosen.

        Returns:
            A new object instance initialized with the field values of the current object.

        Raises:
            ObjectNotRegisteredError: If the object is not registered in dataClay.
            KeyError: If the backend_id is not registered in dataClay.
        """

        if not self._dc_is_registered:
            raise ObjectNotRegisteredError(self._dc_id)

        object_copy = get_runtime().get_object_copy(self, recursive)

        # NOTE: This will keep a reference to the original version, and all the previous versions
        try:
            # If making a version of a version.
            # This works because _dc_original only exists in versions
            object_copy._dc_original = self._dc_original
            # We append here, because the self is a version since it has _dc_original
            object_copy._dc_versions = self._dc_versions + [self]
        except AttributeError:
            object_copy._dc_original = self
            object_copy._dc_versions = []

        get_runtime().make_persistent(object_copy, None, backend_id, recursive)
        return object_copy

    def consolidate_version(self):
        """Consolidate the current version of the object with the original one."""

        original_object_id = self._dc_original._dc_id
        get_runtime().proxify_object(self._dc_original, original_object_id)

        for version in self._dc_versions:
            get_runtime().proxify_object(version, original_object_id)

        get_runtime().change_object_id(self, original_object_id)

    def get_id(self):
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

    #################################
    # Extradata getters and setters #
    #################################

    def _add_replica_location(self, new_replica_location):
        replica_locations = self._dc_replica_backend_ids
        if replica_locations is None:
            replica_locations = list()
            self._dc_replica_backend_ids = replica_locations
        replica_locations.append(new_replica_location)

    def _remove_replica_location(self, old_replica_location):
        replica_locations = self._dc_replica_backend_ids
        replica_locations.remove(old_replica_location)

    def _clear_replica_locations(self):
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

        # TODO: If its a version, use the original object id.

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
