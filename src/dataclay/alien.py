import asyncio
import functools
import logging
from typing import ClassVar, Generic, Type, TypeVar

from .config import get_runtime
from .dataclay_object import DataClayObject
from .event_loop import get_dc_event_loop

ignore_fields = frozenset(
    [
        "__class__",
        "__getattr__",
        "__getattribute__",
        "__setattr__",
        "__delattr__",
        "__dir__",
        "__repr__",
        "__slots__",
        "__weakref__",
        "__init__",
        "__new__",
        "__getstate__",
        "__setstate__",
        "__reduce__",
        "__reduce_ex__",
        "__dict__",
        "__module__",
    ]
)

local_fields = frozenset(
    ["_dc_meta", "_dc_is_local", "_dc_is_loaded", "_dc_is_registered", "_dc_is_replica", "__dict__"]
)


logger = logging.getLogger(__name__)


def virtualactivemethod(func):
    """Internal decorator for AlienDataClayObject methods.

    This is based on activemethod but with slight changes to accomodate its
    usage.
    """

    @functools.wraps(func)
    def wrapper(self: AlienDataClayObject, *args, **kwargs):
        try:
            # Example to make __init__ active:
            # if func.__name__ == "__init__" and not self._dc_is_registered:
            #     self.make_persistent()

            dc_meta = object.__getattribute__(self, "_dc_meta")

            if object.__getattribute__(self, "_dc_is_local"):
                logger.debug(
                    "(%s) Calling virtualactivemethod '%s' locally", dc_meta.id, func.__name__
                )

                return func(self._dc_base_object, *args, **kwargs)
            else:
                logger.debug(
                    "(%s) Calling virtualactivemethod '%s' remotely", dc_meta.id, func.__name__
                )

                # TODO what if it is a coroutinefunction?
                return asyncio.run_coroutine_threadsafe(
                    get_runtime().call_remote_method(self, func.__name__, args, kwargs),
                    get_dc_event_loop(),
                ).result()
        except Exception:
            logger.debug("Error calling virtualactivemethod '%s'", func.__name__, exc_info=True)
            raise

    # wrapper.is_activemethod = True
    return wrapper


T = TypeVar("T")


class AlienDataClayObject(DataClayObject, Generic[T]):
    """Base class for having Alien Persistent Objects.

    This class is used to create a proxy-like Python object and leverage
    dataClay features on non-DataClayObject instances.

    Using this class has certain limitations, but it can be used under certain
    scenarios in which having a DataClayObject class is challenging or
    inappropriate. For example, this class can accommodate the use of NumPy
    arrays or Pandas DataFrames.
    """

    _dc_proxy_classes_cache: ClassVar[dict] = dict()
    _dc_base_object: T

    @classmethod
    def _create_class_proxy(cls, extraneous_class: Type[T]) -> Type[T]:
        """Create a new class (type instance) for an extraneous class.

        This class method will be called once per class to create the
        specialized proxy class mimicking the extraneous one. This method
        introspects the extraneous class and creates the appropriate active
        methods.
        """
        try:
            return cls._dc_proxy_classes_cache[extraneous_class]
        except KeyError:
            cls_namespace = {}
            for name in dir(extraneous_class):
                subject = getattr(extraneous_class, name)
                if callable(subject) and name not in ignore_fields:
                    cls_namespace[name] = virtualactivemethod(subject)

            new_cls = type(
                "%s[%s.%s]"
                % (cls.__name__, extraneous_class.__module__, extraneous_class.__name__),
                (cls,),
                cls_namespace,
            )
            cls._dc_proxy_classes_cache[extraneous_class] = new_cls
            return new_cls

    def __new__(cls, obj: T, *args, **kwargs):
        """Creates a AlienDataClayObject instance referencing `obj`."""
        proxy_class = cls._create_class_proxy(obj.__class__)

        instance = DataClayObject.__new__(proxy_class)
        object.__getattribute__(instance, "_dc_meta").class_name = (
            f"AlienDataClayObject[{type(obj).__module__}.{type(obj).__name__}]"
        )
        object.__setattr__(instance, "_dc_base_object", obj)
        return instance

    def __getattr__(self, name):
        if name in local_fields:
            return object.__getattribute__(self, name)
        elif object.__getattribute__(self, "_dc_is_local"):
            logger.debug("local get")
            if not object.__getattribute__(self, "_dc_is_loaded"):
                asyncio.run_coroutine_threadsafe(
                    get_runtime().data_manager.load_object(self), get_dc_event_loop()
                ).result()
            return getattr(self._dc_base_object, name)
        else:
            logger.debug("local get")

            return asyncio.run_coroutine_threadsafe(
                get_runtime().call_remote_method(self, "__getattribute__", (name,), {}),
                get_dc_event_loop(),
            ).result()

    def __setattr__(self, name, value):
        if name in local_fields:
            return object.__setattr__(self, name, value)
        elif object.__getattribute__(self, "_dc_is_local"):
            logger.debug("local set")
            if not object.__getattribute__(self, "_dc_is_loaded"):
                asyncio.run_coroutine_threadsafe(
                    get_runtime().data_manager.load_object(self), get_dc_event_loop()
                ).result()
            setattr(self._dc_base_object, name, value)
        else:
            logger.debug("remote set")
            return asyncio.run_coroutine_threadsafe(
                get_runtime().call_remote_method(self, "__setattr__", (name, value), {}),
                get_dc_event_loop(),
            ).result()

    def __delattr__(self, name: str):
        if name in local_fields:
            raise SystemError("Should not delete local field %s" % name)
        elif object.__getattribute__(self, "_dc_is_local"):
            logger.debug("local del")
            if not object.__getattribute__(self, "_dc_is_loaded"):
                asyncio.run_coroutine_threadsafe(
                    get_runtime().data_manager.load_object(self), get_dc_event_loop()
                ).result()
            delattr(self._dc_base_object, name)
        else:
            logger.debug("remote del")
            return asyncio.run_coroutine_threadsafe(
                get_runtime().call_remote_method(self, "__delattr__", (name,), {}),
                get_dc_event_loop(),
            ).result()

    def __getstate__(self):
        return self._dc_base_object

    def __setstate__(self, state):
        object.__setattr__(self, "_dc_base_object", state)
