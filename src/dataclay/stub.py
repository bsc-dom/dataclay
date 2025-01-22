import asyncio
import logging
from typing import NamedTuple

from .dataclay_object import DataClayObject
from .event_loop import get_dc_event_loop
# Note that session_var is only needed in _get_by_alias, and maybe should be moved to DataClayRuntime (maybe, TODO, check)
from .config import get_runtime, session_var

local_fields = frozenset(
    ["_dc_stub_classname", "_dc_meta", "_dc_is_local", "_dc_is_loaded", "_dc_is_registered", "_dc_is_replica", "__dict__"]
)

logger = logging.getLogger(__name__)


class StubInfo(NamedTuple):
    classname: str
    properties: list[str]
    activemethods: list[str]


def stubmethodwrapper(basename, method_name):
    def remote_calling(self, *args, **kwargs):
        logger.debug(
            "Calling activemethod '%s' from stub %r", method_name, self
        )

        return asyncio.run_coroutine_threadsafe(
            get_runtime().call_remote_method(self, method_name, args, kwargs),
            get_dc_event_loop()
        ).result()

    remote_calling.__name__ = method_name
    remote_calling.__qualname__ = f"{basename}.{method_name}"
    return remote_calling


class _StubMetaClass(type):
    cached_classes = {}

    def __getitem__(cls, key):
        # TODO: `properties` and `activemethods` should be retrieved from dataClay
        classname, properties, activemethods = key
        # so only classname is used as the key for the StubDataClayObject["<classname>"]
        if classname not in cls.cached_classes:
            # Prepare the StubInfo tuple
            stub_info = StubInfo(
                classname=classname,
                properties=properties,
                activemethods=activemethods,
            )

            # The class dictionary containing all the methods
            _, basename = classname.rsplit(".", 1)
            clsdict = {
                method_name: stubmethodwrapper(basename, method_name)
                for method_name in activemethods
            }
            # and also the stub info in its proper place
            clsdict["_dc_stub_info"] = stub_info

            # That should be enough for creating the class
            cls.cached_classes[classname] = type(
                f"StubDataClayObject[{classname}]",
                (StubDataClayObject,),
                clsdict,
            )

        return cls.cached_classes[classname]


class StubDataClayObject(DataClayObject, metaclass=_StubMetaClass):
    _dc_stub_info: StubInfo

    @classmethod
    def _check_stub_info(cls):
        if not hasattr(cls, "_dc_stub_info"):
            raise TypeError("Need to specify class first: StubDataClayObject[\"<classname>\"]")

    def __init__(self, *args, **kwargs):
        self._check_stub_info()

        raise NotImplementedError("TODO: Remote instantiation is not implemented yet")

    @classmethod
    async def _get_by_alias(cls, alias: str, dataset_name: str = None):
        # This is adapted from DataClayRuntime.get_object_by_alias
        # TODO: Maybe this should be done there instead? Not sure.
        if dataset_name is None:
            dataset_name = session_var.get()["dataset_name"]
        object_md = await get_runtime().metadata_service.get_object_md_by_alias(alias, dataset_name)

        new_stub = cls.__new__(cls)
        new_stub._dc_meta = object_md
        new_stub._dc_is_local = False
        new_stub._dc_is_replica = False
        new_stub._dc_is_loaded = False
        new_stub._dc_is_registered = True

        return new_stub

    @classmethod
    def get_by_alias(cls, alias: str, dataset_name: str = None):
        """Create a new instance of the stub class by alias.
        
        This class overrides the behavior of :meth:`~dataclay.DataClayObject.get_by_alias`
        and creates stub instance from the alias.

        Args:
            alias: The alias of the object to retrieve.
            dataset_name: Optional. The name of the dataset where the alias is stored.
                          If not provided, the active dataset is used.

        Returns:
            A stub instance of the object associated with the given alias.
        """
        cls._check_stub_info()

        return asyncio.run_coroutine_threadsafe(
            cls._get_by_alias(alias, dataset_name), get_dc_event_loop()
        ).result()

    def __getattr__(self, name):
        if name in local_fields:
            return object.__getattribute__(self, name)
        elif name in self._dc_stub_info.properties:
            logger.debug("remote get")

            return asyncio.run_coroutine_threadsafe(
                get_runtime().call_remote_method(self, "__getattribute__", (name,), {}),
                get_dc_event_loop(),
            ).result()
        elif name in self._dc_stub_info.activemethods:
            return StubActiveMethodHelper(self, name)
        else:
            raise AttributeError(f"Property {name} is not defined in {self._dc_stub_info.classname}")

    def __setattr__(self, name, value):
        if name in local_fields:
            return object.__setattr__(self, name, value)
        elif name in self._dc_stub_info.properties:
            logger.debug("remote set")

            return asyncio.run_coroutine_threadsafe(
                get_runtime().call_remote_method(self, "__setattr__", (name, value), {}),
                get_dc_event_loop(),
            ).result()
        else:
            raise AttributeError(f"Property {name} is not defined in {self._dc_stub_info.classname}")

    def __delattr__(self, name):
        if name in local_fields:
            raise SystemError("Should not delete local field %s" % name)
        elif name in self._dc_stub_info.properties:
            logger.debug("remote del")
            return asyncio.run_coroutine_threadsafe(
                get_runtime().call_remote_method(self, "__delattr__", (name,), {}),
                get_dc_event_loop(),
            ).result()
        else:
            raise AttributeError(f"Property {name} is not defined in {self._dc_stub_info.classname}")
