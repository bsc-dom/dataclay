"""Management of Python Classes.

This module is responsible of management of the Class Objects. A central Python
Metaclass is responsible of Class (not object) instantiation.

Note that this managers also includes most serialization/deserialization code
related to classes and function call parameters.
"""

from __future__ import annotations

import asyncio
import functools
import inspect
import logging
import threading
import traceback
from collections import ChainMap

from dataclay.config import settings

try:
    from inspect import get_annotations
except ImportError:
    # This should happen only on Python 3.9, and the package should have been installed
    # (see dependencies on pyproject.toml)
    from get_annotations import get_annotations

from typing import TYPE_CHECKING, Annotated, Any, Awaitable, Optional, Type, TypeVar, get_origin

from dataclay.annotated import LocalOnly, PropertyTransformer
from dataclay.exceptions import *
from dataclay.metadata.kvdata import ObjectMetadata
from dataclay.runtime import get_dc_event_loop, get_runtime, lock_manager
from dataclay.utils.telemetry import trace

if TYPE_CHECKING:
    from uuid import UUID

DC_PROPERTY_PREFIX = "_dc_property_"
Sentinel = object()


tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)

T = TypeVar("T")


def activemethod(func):
    """Decorator for DataClayObject active methods."""

    @functools.wraps(func)
    def wrapper(self: DataClayObject, *args, **kwargs):
        try:
            # Example to make __init__ active:
            # if func.__name__ == "__init__" and not self._dc_is_registered:
            #     self.make_persistent()

            if self._dc_is_local:
                logger.debug(
                    "(%s) Calling activemethod '%s' locally", self._dc_meta.id, func.__name__
                )

                # NOTE: When calling an activemethod (from a backend), we must acquire the lock
                # so the object is not modified/unload by another coroutine. This is only important
                # for the non-dc properties. If the object has only dc_properties, this is no
                # relevant since the object will be reloaded when accessing this properties.
                # TODO: Check if this increaes the overhead. If so, maybe remove the lock.
                # Only acquire the reader lock, so multiple clients can perform multiple calls on
                # the same object methods.
                # NOTE: Using run_dc_coroutine to run the coroutine in the main event loop.
                # This means that all activemethods should be run in another thread.
                # NOTE: If running in a non-initialized client, there won't be any event loop setup.
                return func(self, *args, **kwargs)

                # TODO: TO SOLVE
                if get_dc_event_loop() is None:
                    logger.warning("1111111")
                    return func(self, *args, **kwargs)
                else:
                    logger.warning("2222222")
                    lock = lock_manager.get_lock(self._dc_meta.id)
                    logger.warning(lock)
                    run_dc_coroutine(lock.reader_lock.acquire)
                    try:
                        result = func(self, *args, **kwargs)
                    finally:
                        lock.reader_lock.release()
                    return result
            else:
                logger.debug(
                    "(%s) Calling activemethod '%s' remotely", self._dc_meta.id, func.__name__
                )

                if inspect.iscoroutinefunction(func):
                    return get_runtime().call_remote_method(self, func.__name__, args, kwargs)
                else:
                    loop = get_dc_event_loop()
                    return loop.run_until_complete(
                        get_runtime().call_remote_method(self, func.__name__, args, kwargs)
                    )
        except Exception:
            traceback.print_exc()
            raise

    # wrapper.is_activemethod = True
    return wrapper


def run_dc_coroutine(func: Awaitable, *args, **kwargs):
    loop = get_dc_event_loop()
    if loop.is_running():
        # If the event loop is running, we can't call run_until_complete.
        if loop._thread_id == threading.get_ident():
            # From the same thread must use the async version of the method
            # Happens only(?) inside inner dataClay code.
            raise RuntimeError(
                "Trying to run non-async dataClay API method from inside the event loop."
                "Use the async version of the method or run it from outside the event loop."
            )
        else:
            # Event loop is running in another thread
            # Only(?) happens when backend run dataClay methods inside an activemethod
            # And when serializing dataClay objects with pickle
            future = asyncio.run_coroutine_threadsafe(func(*args, **kwargs), loop)
            return future.result()
    else:
        # If the event loop is not running, we can call run_until_complete.
        # This should only happen from user SyncClient calls. All inner code
        # should be async with a running event loop.
        return loop.run_until_complete(func(*args, **kwargs))


class DataClayProperty:
    __slots__ = "name", "dc_property_name", "default_value", "transformer"

    def __init__(
        self,
        name: str,
        default_value: Any = Sentinel,
        transformer: PropertyTransformer = None,
    ):
        self.name = name
        self.dc_property_name = DC_PROPERTY_PREFIX + name
        self.default_value = default_value
        self.transformer = transformer

    def __get__(self, instance: DataClayObject, owner):
        """
        | is_local | is_load |
        | True     | True    |  B (heap) or C (not persistent)
        | True     | False   |  B (stored)
        | False    | True    |  -
        | False    | False   |  B (remote) or C (persistent)
        """
        if instance._dc_is_local:
            logger.debug(
                "(%s) Getting dc_property '%s.%s' locally",
                instance._dc_meta.id,
                instance.__class__.__name__,
                self.name,
            )

            # If the object is local and loaded, we can access the attribute directly
            if not instance._dc_is_loaded:
                # NOTE: Should be called from another thread.
                # Should only happen inside activemethods.
                run_dc_coroutine(get_runtime().data_manager.load_object, instance)
            try:
                attr = getattr(instance, self.dc_property_name)
            except AttributeError as e:
                if self.default_value is Sentinel:
                    e.args = (e.args[0].replace(self.dc_property_name, self.name),)
                    raise e
                return self.default_value
            if self.transformer is None:
                return attr
            else:
                return self.transformer.getter(attr)
        else:
            logger.debug(
                "(%s) Getting dc_property '%s.%s' remotely",
                instance._dc_meta.id,
                instance.__class__.__name__,
                self.name,
            )

            loop = get_dc_event_loop()
            if loop.is_running():
                # NOTE: This will make attribute access for a user's AsyncClient or from our
                # inner code, to be async. This could not be desired in the future, since
                # it is not the expected behaviour of python properties.
                # TODO: Find a better way to handle this.
                return get_runtime().call_remote_method(
                    instance, "__getattribute__", (self.name,), {}
                )
            else:
                return loop.run_until_complete(
                    get_runtime().call_remote_method(instance, "__getattribute__", (self.name,), {})
                )

    def __set__(self, instance: DataClayObject, value):
        """Setter for the dataClay property

        See the __get__ method for the basic behavioural explanation.
        """
        if instance._dc_is_local:
            logger.debug(
                "(%s) Setting dc_property '%s.%s=%s' locally",
                instance._dc_meta.id,
                instance.__class__.__name__,
                self.name,
                value,
            )

            if not instance._dc_is_loaded:
                # NOTE: (Same as in __get__ method)
                run_dc_coroutine(get_runtime().data_manager.load_object, instance)
            if self.transformer is not None:
                value = self.transformer.setter(value)
            setattr(instance, self.dc_property_name, value)
        else:
            logger.debug(
                "(%s) Setting dc_property '%s.%s=%s' remotely",
                instance._dc_meta.id,
                instance.__class__.__name__,
                self.name,
                value,
            )

            loop = get_dc_event_loop()
            if loop.is_running():
                # NOTE: Same problem as in __get__ method.
                # TODO: Find a better way to handle this.
                return get_runtime().call_remote_method(
                    instance, "__setattr__", (self.name, value), {}
                )
            else:
                return loop.run_until_complete(
                    get_runtime().call_remote_method(
                        instance, "__setattr__", (self.name, value), {}
                    )
                )

    def __delete__(self, instance: DataClayObject):
        """Deleter for the dataClay property"""
        logger.debug(
            "(%s) Deleting property %s.%s",
            instance._dc_meta.id,
            instance.__class__.__name__,
            self.name,
        )

        if instance._dc_is_local:
            logger.debug("Local")
            delattr(instance, self.dc_property_name)
        else:
            logger.debug("Remote")
            get_runtime().call_remote_method(instance, "__delattr__", (self.name,), {})


class DataClayObject:
    """Main class for Persistent Objects.

    Objects that has to be made persistent should derive this class (either
    directly, through the StorageObject alias, or through a derived class).
    """

    _dc_meta: ObjectMetadata

    _dc_is_local: bool = True
    _dc_is_loaded: bool = True
    _dc_is_registered: bool = False
    _dc_is_replica: bool = False

    def __init_subclass__(cls) -> None:
        """Defines a @property for each annotatted attribute"""
        all_annotations = ChainMap(*(get_annotations(c) for c in cls.__mro__))

        for property_name, property_type in all_annotations.items():
            is_local_only = False
            transformer = None

            if property_name.startswith("_dc_"):
                continue
            if get_origin(property_type) is Annotated:
                for annotation in property_type.__metadata__:
                    if isinstance(annotation, PropertyTransformer):
                        transformer = annotation
                    if isinstance(annotation, LocalOnly):
                        is_local_only = True

            if is_local_only:
                continue
            if hasattr(cls, property_name):
                default_value = getattr(cls, property_name)
                dataclay_property = DataClayProperty(property_name, default_value, transformer)
            else:
                dataclay_property = DataClayProperty(property_name, transformer=transformer)
            setattr(cls, property_name, dataclay_property)

    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls)
        obj._dc_meta = ObjectMetadata(class_name=cls.__module__ + "." + cls.__name__)

        logger.debug(
            "(%s) Creating new dc_object '%s' args=%s, kwargs=%s",
            obj._dc_meta.id,
            cls.__name__,
            args,
            kwargs,
        )

        # If the object is being created in a backend, it should be made persistent immediately
        # This should only happen when instantiating a dataClay object from an activemethod,
        # The activemethod must had been called in another thread using an executor. Therefore,
        # there is not running event loop in the current thread, and we can use run_coroutine_threadsafe
        # to the main dc_running_loop.
        # TODO: This same logic applies to all DataClayObject methods that are called withing an activemethod.
        if get_runtime() and get_runtime().is_backend:
            logger.debug("(%s) Calling implicit make_persistent", obj._dc_meta.id)

            # TODO: Option to make an eventual call to make_persistent async
            # loop.create_task(obj.a_make_persistent())
            obj.make_persistent()
            # loop = get_dc_event_loop()
            # t = asyncio.run_coroutine_threadsafe(obj.make_persistent(), loop)
            # t.result()

        return obj

    @classmethod
    def new_proxy_object(cls):
        obj = super().__new__(cls)
        obj._dc_meta = ObjectMetadata(class_name=cls.__module__ + "." + cls.__name__)
        return obj

    @property
    def _dc_properties(self) -> dict[str, Any]:
        """Returns __dict__ with only _dc_property_ attributes"""
        return {k: v for k, v in vars(self).items() if k.startswith(DC_PROPERTY_PREFIX)}

    @property
    def _dc_state(self) -> tuple[dict, Any]:
        """Returns the object state"""
        state = {"_dc_meta": self._dc_meta}
        if hasattr(self, "__getstate__") and hasattr(self, "__setstate__"):
            return state, self.__getstate__()
        else:
            state.update(self._dc_properties)
            return state, None

    @property
    def _dc_all_backend_ids(self) -> set[UUID]:
        """Returns a set with all the backend ids where the object is stored"""
        if self._dc_meta.master_backend_id is None:
            return set()
        return self._dc_meta.replica_backend_ids | {self._dc_meta.master_backend_id}

    @property
    def is_persistent(self) -> bool:
        """Whether the object is registered in the dataClay system or not."""
        return self._dc_is_registered

    @property
    def backends(self) -> set[UUID]:
        """Returns a set with all the backend ids where the object is stored"""
        return self._dc_all_backend_ids

    def _clean_dc_properties(self):
        """
        Used to free up space when the client or backend lose ownership of the objects;
        or the object is being stored and unloaded
        """
        self.__dict__ = {
            k: v for k, v in vars(self).items() if not k.startswith(DC_PROPERTY_PREFIX)
        }

    @tracer.start_as_current_span("getID")
    def getID(self) -> Optional[str]:
        """Return the JSON-encoded metadata of the persistent object for COMPSs.

        If the object is NOT persistent, then this method returns None.
        """
        if self._dc_is_registered:
            return self._dc_meta.model_dump_json()
        else:
            return None

    @tracer.start_as_current_span("sync")
    async def a_sync(self):
        """Synchronizes the object metadata

        It will always retrieve the current metadata from the kv database.
        It won't update local changes to the database.

        Raises:
            ObjectNotRegisteredError: If the object is not registered.
            ObjectIsMasterError: If the object is the master.
        """
        if not self._dc_is_registered:
            raise ObjectNotRegisteredError(self._dc_meta.id)
        if self._dc_is_local and not self._dc_is_replica:
            raise ObjectIsMasterError(self._dc_meta.id)
        await get_runtime().sync_object_metadata(self)

    def sync(self):
        return run_dc_coroutine(self.a_sync)

    ###########################
    # Object Oriented Methods #
    ###########################

    @tracer.start_as_current_span("make_persistent")
    async def a_make_persistent(
        self, alias: Optional[str] = None, backend_id: Optional[UUID] = None
    ):
        """Makes the object persistent.

        Args:
            alias: Alias of the object. If None, the object will not have an alias.
            backend_id: ID of the backend where the object will be stored. If None, the object
                will be stored in a random backend.

        Raises:
            KeyError: If the backend_id is not registered in dataClay.
        """
        if self._dc_is_registered:
            logger.info("(%s) Object is already registered", self._dc_meta.id)
            if backend_id:
                await self.a_move(backend_id)
            if alias:
                await self.a_add_alias(alias)
        else:
            await get_runtime().make_persistent(self, alias=alias, backend_id=backend_id)

    def make_persistent(self, alias: Optional[str] = None, backend_id: Optional[UUID] = None):
        return run_dc_coroutine(self.a_make_persistent, alias, backend_id)

    @classmethod
    @tracer.start_as_current_span("get_by_id")
    async def a_get_by_id(cls, object_id: UUID) -> DataClayObject:
        """Returns the object with the given id.

        Args:
            object_id: ID of the object.

        Returns:
            The object with the given id.

        Raises:
            DoesNotExistError: If the object does not exist.
        """
        return await get_runtime().get_object_by_id(object_id)

    @classmethod
    def get_by_id(cls, object_id: UUID) -> DataClayObject:

        # WARNING: This method must not be called from the same thread as the running event loop
        # or it will block the event loop. When unserializing dataClay objects, use "await dcloads"
        # if possible. Only use "pickle.loads" if you are sure that the event loop is not running.
        # "pickle.loads" of dataClay objects is calling this method behind. With `dcloads` this method
        # will be called in another thread, so it will not block the event loop.

        return run_dc_coroutine(cls.a_get_by_id, object_id)

    @classmethod
    @tracer.start_as_current_span("get_by_alias")
    async def a_get_by_alias(cls: Type[T], alias: str, dataset_name: str = None) -> T:
        """Returns the object with the given alias.

        Args:
            alias: Alias of the object.
            dataset_name: Name of the dataset where the alias is stored. If None, the active dataset is used.

        Returns:
            The object with the given alias.

        Raises:
            DoesNotExistError: If the alias does not exist.
            DatasetIsNotAccessibleError: If the dataset is not accessible.
        """
        return await get_runtime().get_object_by_alias(alias, dataset_name)

    @classmethod
    def get_by_alias(cls: Type[T], alias: str, dataset_name: str = None) -> T:
        return run_dc_coroutine(cls.a_get_by_alias, alias, dataset_name)

    @tracer.start_as_current_span("add_alias")
    async def a_add_alias(self, alias: str):
        """Adds an alias to the object.

        Args:
            alias: Alias to be added.

        Raises:
            ObjectNotRegisteredError: If the object is not registered.
            AttributeError: If the alias is an empty string.
            DataClayException: If the alias already exists.
        """
        await get_runtime().add_alias(self, alias)

    def add_alias(self, alias: str):
        return run_dc_coroutine(self.a_add_alias, alias)

    @tracer.start_as_current_span("get_aliases")
    async def a_get_aliases(self) -> set[str]:
        """Returns a set with all the aliases of the object."""
        aliases = await get_runtime().get_all_alias(self._dc_meta.dataset_name, self._dc_meta.id)
        return set(aliases)

    def get_aliases(self) -> set[str]:
        return run_dc_coroutine(self.a_get_aliases)

    @classmethod
    @tracer.start_as_current_span("delete_alias")
    async def a_delete_alias(cls, alias: str, dataset_name: str = None):
        """Removes the alias linked to an object.

        If this object is not referenced starting from a root object and no active session is
        accessing it, the garbage collector will remove it from the system.

        Args:
            alias: Alias to be removed.
            dataset_name: Name of the dataset where the alias is stored. If None, the active dataset is used.

        Raises:
            DoesNotExistError: If the alias does not exist.
            DatasetIsNotAccessibleError: If the dataset is not accessible.
        """
        await get_runtime().delete_alias(alias, dataset_name=dataset_name)

    @classmethod
    def delete_alias(cls, alias: str, dataset_name: str = None):
        return run_dc_coroutine(cls.a_delete_alias, alias, dataset_name)

    @tracer.start_as_current_span("move")
    async def a_move(self, backend_id: UUID, recursive: bool = False, remotes: bool = True):
        """Moves the object to the specified backend.

        If the object is not registered, it will be registered with all its references
        to the corresponding backend

        Args:
            backend_id: Id of the backend where the object will be moved.
            recursive: If True, all objects referenced by this object registered in the
                same backend will also be moved.
            remotes: If True (default), when recursive is True the remote references will
                also be moved. Otherwise only the local references are moved.

        Raises:
            KeyError: If the backend_id is not registered in dataClay.
        """
        if not self._dc_is_registered:
            await self.a_make_persistent(backend_id=backend_id)
        else:
            await get_runtime().send_objects([self], backend_id, False, recursive, remotes)

    def move(self, backend_id: UUID, recursive: bool = False, remotes: bool = True):
        return run_dc_coroutine(self.a_move, backend_id, recursive, remotes)

    ##############
    # Versioning #
    ##############

    @tracer.start_as_current_span("new_version")
    async def a_new_version(
        self, backend_id: UUID = None, recursive: bool = False
    ) -> DataClayObject:
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
        return await get_runtime().new_object_version(self, backend_id)

    def new_version(self, backend_id: UUID = None, recursive: bool = False) -> DataClayObject:
        return run_dc_coroutine(self.a_new_version, backend_id, recursive)

    @tracer.start_as_current_span("consolidate_version")
    async def a_consolidate_version(self):
        """Consolidate the current version of the object with the original one.

        Raises:
            ObjectIsNotVersionError: If the object is not a version.
        """
        await get_runtime().consolidate_version(self)

    def consolidate_version(self):
        return run_dc_coroutine(self.a_consolidate_version)

    ###########
    # Replica #
    ###########

    @tracer.start_as_current_span("new_replica")
    async def a_new_replica(
        self, backend_id: UUID = None, recursive: bool = False, remotes: bool = True
    ):
        await get_runtime().new_object_replica(self, backend_id, recursive, remotes)

    def new_replica(self, backend_id: UUID = None, recursive: bool = False, remotes: bool = True):
        return run_dc_coroutine(self.a_new_replica, backend_id, recursive, remotes)

    ########################
    # Object Store Methods #
    ########################

    @classmethod
    @tracer.start_as_current_span("dc_clone_by_alias")
    async def dc_clone_by_alias(cls, alias: str, recursive: bool = False) -> DataClayObject:
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
        instance = await cls.a_get_by_alias(alias)
        return await get_runtime().make_object_copy(instance, recursive)

    @tracer.start_as_current_span("dc_clone")
    async def dc_clone(self, recursive: bool = False) -> DataClayObject:
        """Returns a non-persistent object as a copy of the current object.

        Args:
            recursive: When this is set to True, the default behavior is altered so not only current
                object but all of its references are also retrieved locally.

        Returns:
            A new object instance initialized with the field values of the current object.

        Raises:
            ObjectNotRegisteredError: If the object is not registered.
        """
        return await get_runtime().make_object_copy(self, recursive)

    @classmethod
    @tracer.start_as_current_span("dc_update_by_alias")
    async def dc_update_by_alias(cls, alias: str, from_object: DataClayObject):
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

        o = await cls.a_get_by_alias(alias)
        await o.dc_update(from_object)

    @tracer.start_as_current_span("dc_update")
    async def dc_update(self, from_object: DataClayObject):
        """Updates current object with contents of from_object.

        Args:
            from_object: object with the new values to update current object.

        Raises:
            TypeError: If the objects are not of the same type.
        """
        if type(self) != type(from_object):
            raise TypeError("Objects must be of the same type")

        await get_runtime().replace_object_properties(self, from_object)

    @tracer.start_as_current_span("dc_put")
    async def dc_put(self, alias: str, backend_id: UUID = None):
        """Makes the object persistent in the specified backend.

        Args:
            alias: a string that will identify the object in addition to its OID.
                Aliases are unique for dataset.
            backend_id: the backend where the object will be stored. If this parameter is not
                specified, a random backend will be chosen.

        Raises:
            AttributeError: if alias is null or empty.
            AlreadyExistError: If the alias already exists.
            KeyError: If the backend_id is not registered in dataClay.
            ObjectAlreadyRegisteredError: If the object is already registered in dataClay.
        """
        if not alias:
            raise AttributeError("Alias cannot be null or empty")
        await self.a_make_persistent(alias=alias, backend_id=backend_id)

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
        raise Exception("Synchronize need refactor")
        return get_runtime().synchronize(self, DCLAY_SETTER_PREFIX + field_name, value)

    def __repr__(self):
        if self._dc_is_registered:
            return "<%s instance with ObjectID=%s>" % (
                self._dc_meta.class_name,
                self._dc_meta.id,
            )
        else:
            return "<%s volatile instance with ObjectID=%s>" % (
                self._dc_meta.class_name,
                self._dc_meta.id,
            )

    def __eq__(self, other):
        if not isinstance(other, DataClayObject):
            return False

        if not self._dc_is_registered or not other._dc_is_registered:
            return False

        return self._dc_meta.id == other._dc_meta.id

    # FIXME: Think another solution, the user may want to override the method
    def __hash__(self):
        return hash(self._dc_meta.id)

    @activemethod
    def __setUpdate__(
        self, obj: "Any", property_name: str, value: "Any", beforeUpdate: str, afterUpdate: str
    ):
        if beforeUpdate is not None:
            getattr(self, beforeUpdate)(property_name, value)
        object.__setattr__(obj, "%s%s" % ("_dataclay_property_", property_name), value)
        if afterUpdate is not None:
            getattr(self, afterUpdate)(property_name, value)

    def __copy__(self):
        # NOTE: A shallow copy cannot be performed, or has no sense.
        return self
