"""Management of Python Classes.

This module is responsible of management of the Class Objects. A central Python
Metaclass is responsible of Class (not object) instantiation.

Note that this managers also includes most serialization/deserialization code
related to classes and function call parameters.
"""

__author__ = "Alex Barcelo <alex.barcelo@bsc.es>"
__copyright__ = "2016 Barcelona Supercomputing Center (BSC-CNS)"

import functools
import inspect
import logging
import pickle
import re
import traceback
import uuid
from operator import attrgetter

from dataclay_common.managers.object_manager import ObjectMetadata
from dataclay_common.protos.common_messages_pb2 import LANG_PYTHON
from opentelemetry import trace

from dataclay.DataClayObjectExtraData import DataClayClassExtraData, DataClayInstanceExtraData
from dataclay.DataClayObjMethods import dclayMethod
from dataclay.DataClayObjProperties import (
    DCLAY_PROPERTY_PREFIX,
    DataclayProperty,
    PreprocessedProperty,
)
from dataclay.exceptions.exceptions import DataClayException, ImproperlyConfigured
from dataclay.runtime import get_runtime
from dataclay.serialization.lib.DeserializationLibUtils import (
    DeserializationLibUtilsSingleton,
    PersistentLoadPicklerHelper,
)
from dataclay.serialization.lib.SerializationLibUtils import (
    PersistentIdPicklerHelper,
    SerializationLibUtilsSingleton,
)
from dataclay.serialization.python.lang.BooleanWrapper import BooleanWrapper
from dataclay.serialization.python.lang.DCIDWrapper import DCIDWrapper
from dataclay.serialization.python.lang.IntegerWrapper import IntegerWrapper
from dataclay.serialization.python.lang.StringWrapper import StringWrapper
from dataclay.util.classloaders.ClassLoader import load_metaclass
from dataclay.util.management.classmgr.Type import Type
from dataclay.util.management.classmgr.UserType import UserType
from dataclay.util.StubUtils import load_babel_data

# Publicly show the dataClay method decorators

tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)

# For efficiency purposes compile the folowing regular expressions:
# (they return a tuple of two elements)
re_property = re.compile(
    r"(?:^\s*@dclayReplication\s*\(\s*(before|after)Update\s*=\s*'([^']+)'(?:,\s(before|after)Update='([^']+)')?(?:,\sinMaster='(True|False)')?\s*\)\n)?^\s*@ClassField\s+([\w.]+)[ \t]+([\w.\[\]<> ,]+)",
    re.MULTILINE,
)
re_import = re.compile(r"^\s*@d[cC]layImport(?P<from_mode>From)?\s+(?P<import>.+)$", re.MULTILINE)


def _get_object_by_id_helper(object_id, cls, hint):
    """Helper method which can be pickled and used by DataClayObject.__reduce__"""
    return get_runtime().get_object_by_id(object_id, cls, hint)


def activemethod(func):
    """Decorator for DataClayObject active methods"""

    @functools.wraps(func)
    def wrapper_activemethod(self, *args, **kwargs):
        logger.verbose(f"Calling function {func.__name__}")
        try:
            # If the object is not persistent executes the method locally,
            # else, executes the method within the execution environment
            if (
                (get_runtime().is_exec_env() and self._is_loaded)
                or (get_runtime().is_client() and not self._is_persistent)
                or func.__name__ == "__setstate__"  # For Pickle
                or func.__name__ == "__getstate__"  # For Pickle
            ):
                return func(self, *args, **kwargs)
            else:
                return get_runtime().call_active_method(self, func.__name__, args, kwargs)
        except Exception:
            traceback.print_exc()
            raise

    # wrapper_activemethod.is_activemethod = True
    return wrapper_activemethod


class DataClayObject:
    """Main class for Persistent Objects.

    Objects that has to be made persistent should derive this class (either
    directly, through the StorageObject alias, or through a derived class).
    """

    _object_id: uuid.UUID
    _alias: str
    _dataset_name: str
    _class: type
    _class_name: str
    _is_persistent: bool
    _master_ee_id: uuid.UUID
    _replica_ee_ids: list[uuid.UUID]
    _language: int
    _is_read_only: bool
    _is_dirty: bool
    _is_pending_to_register: bool
    _is_loaded: bool
    _owner_session_id: uuid.UUID

    def __init_subclass__(cls) -> None:
        """ "Defines @properties for each annotatted attribute"""
        for property_name in cls.__annotations__:
            setattr(cls, property_name, DataclayProperty(property_name))

    @classmethod
    def new_dataclay_instance(cls, deserializing: bool = False, object_id: uuid.UUID = None):
        """Return a new instance, without calling to the class methods."""
        logger.debug("New dataClay instance (without __call__) of class `%s`", cls.__name__)
        obj = super().__new__(cls)  # this defers the __call__ method
        obj.initialize_object(deserializing=deserializing, object_id=object_id)
        return obj

    @classmethod
    def new_volatile(cls, **kwargs):
        obj = super().__new__(cls)

        new_dict = kwargs

        if get_runtime().is_exec_env():
            # *** Execution Environment flags
            obj._is_pending_to_register = True
            new_dict["_is_persistent"] = True  # All objects in the EE are persistent
            new_dict["_is_loaded"] = True
            new_dict["_is_pending_to_register"] = True
            new_dict["_master_ee_id"] = get_runtime().get_hint()  # It should be in kwargs

        obj.initialize_object(**new_dict)
        return obj

    @classmethod
    def new_persistent(cls, object_id, master_ee_id):
        obj = super().__new__(cls)

        new_dict = {}
        new_dict["_is_persistent"] = True
        new_dict["_object_id"] = object_id
        new_dict["_master_ee_id"] = master_ee_id

        if get_runtime().is_exec_env():
            # *** Execution Environment flags
            # by default, loaded = true for volatiles created inside executions
            # this function (initialize as persistent) is used for objects being
            # deserialized and therefore they might be unloaded
            # same happens for pending to register flag.
            new_dict["_is_loaded"] = False
            new_dict["_is_pending_to_register"] = False

        obj.initialize_object(**new_dict)
        return obj

    def __new__(cls, *args, **kwargs):
        logger.debug(f"Crated new dataclay object with args={args}, kwargs={kwargs}")
        obj = super().__new__(cls)
        obj.initialize_object()
        return obj

    def initialize_object(self, deserializing=False, **kwargs):
        """Initializes the object"""

        # Populate default internal fields
        self._object_id = uuid.uuid4()
        self._alias = None
        self._dataset_name = get_runtime().session.dataset_name
        self._class = self.__class__
        self._class_name = self.__class__.__module__ + "." + self.__class__.__name__
        self._is_persistent = False
        self._master_ee_id = (
            get_runtime().get_hint()
        )  # May be replaced if instantiating a thing object from different ee
        self._replica_ee_ids = []
        self._language = LANG_PYTHON
        self._is_read_only = False
        self._is_dirty = False
        self._is_pending_to_register = False
        self._is_loaded = False
        self._owner_session_id = (
            get_runtime().session.id
        )  # May be removed to instantiate dc object without init()

        # Update object dict with custome kwargs
        self.__dict__.update(kwargs)

        # Add instance to heap
        get_runtime().add_to_heap(self)

        if not deserializing:
            # object created during executions is volatile.
            self.initialize_object_as_volatile()

    @property
    def dataclay_id(self):
        return self._object_id

    @property
    def dataset(self):
        return self._dataset_name

    def initialize_object_as_persistent(self):
        """Initializes the object as a persistent

        Flags for "persistent" state might be different in EE and client.
        """
        # TODO: improve this using an specialization (dgasull)
        self._is_persistent = True

        if get_runtime().is_exec_env():
            # *** Execution Environment flags
            # by default, loaded = true for volatiles created inside executions
            # this function (initialize as persistent) is used for objects being
            # deserialized and therefore they might be unloaded
            # same happens for pending to register flag.
            self._is_loaded = False
            self._is_pending_to_register = False

    def initialize_object_as_volatile(self):
        """Initialize object with state 'volatile' with proper flags.

        Usually, volatile state is created by a stub, app, exec, class,..
        See same function in DataClayExecutionObject for a different initialization.
        This design is intended to be clear with object state.
        """
        # TODO: improve this using an specialization (dgasull)
        if get_runtime().is_exec_env():
            # *** Execution Environment flags
            self._is_persistent = True  # All objects in the EE are persistent
            self._is_loaded = True
            self._is_pending_to_register = True
            # self._master_ee_id = get_runtime().get_hint()

    def new_replica(self, backend_id=None, recursive=True):
        return get_runtime().new_replica(
            self._object_id, self._master_ee_id, backend_id, None, recursive
        )

    def new_version(self, backend_id=None, recursive=True):
        return get_runtime().new_version(
            self._object_id,
            self._master_ee_id,
            self._class_name,
            self._dataset_name,
            backend_id,
            None,
            recursive,
        )

    def consolidate_version(self):
        """Consolidate: copy contents of current version object to original object"""
        return get_runtime().consolidate_version(self._object_id, self._master_ee_id)

    def make_persistent(self, alias=None, backend_id=None, recursive=True):

        with tracer.start_as_current_span(
            "make_persistent",
            attributes={"alias": str(alias), "backend_id": str(backend_id), "recursive": recursive},
        ) as span:
            if alias == "":
                raise AttributeError("Alias cannot be empty")
            get_runtime().make_persistent(
                self, alias=alias, backend_id=backend_id, recursive=recursive
            )

    def get_execution_environments_info(self):
        return get_runtime().ee_infos

    @classmethod
    def dc_clone_by_alias(cls, alias, recursive=False):
        o = cls.get_by_alias(alias)
        return o.dc_clone(recursive)

    def dc_clone(self, recursive=False):
        """
        @postcondition: Returns a non-persistent object as a copy of the current object
        @return: DataClayObject non-persistent instance
        """
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

    def set_all(self, from_object):
        raise ("set_all need to be refactored")
        properties = sorted(
            self.get_class_extradata().properties.values(), key=attrgetter("position")
        )

        logger.verbose("Set all properties from object %s", from_object._object_id)

        for p in properties:
            value = getattr(from_object, p.name)
            setattr(self, p.name, value)

    def getID(self):
        """Return the string representation of the persistent object for COMPSs.

        dataClay specific implementation: The objects are internally represented
        through ObjectID, which are UUID. In addition to that, some extra fields
        are added to the representation. Currently, a "COMPSs ID" will be:

            <objectID>:<backendID|empty>:<classID>

        In which all ID are UUID and the "hint" (backendID) can be empty.

        If the object is NOT persistent, then this method returns None.
        """
        if self._is_persistent:
            hint = self._master_ee_id or ""

            return "%s:%s:%s" % (
                self._object_id,
                hint,
                None,  # self.get_class_extradata().class_id, TODO: Use class_name
            )
        else:
            return None

    @classmethod
    def get_object_by_id(cls, object_id, *args, **kwargs):
        return get_runtime().get_object_by_id(object_id, *args, **kwargs)

    @classmethod
    def get_by_alias(cls, alias, dataset_name=None):
        # NOTE: "safe" was removed. The object_id cannot be obtained from alias string.
        # NOTE: The alias is unique for each dataset. dataset_name is added. If none,
        #       the default_dataset is used.
        return get_runtime().get_object_by_alias(alias, dataset_name)

    @classmethod
    def delete_alias(cls, alias, dataset_name=None):
        get_runtime().delete_alias_in_dataclay(alias, dataset_name=dataset_name)

    # BUG: Python don't have method overloading
    # def delete_alias(self):
    #     get_runtime().delete_alias(self)

    @property
    def metadata(self):
        object_md = ObjectMetadata(
            self._object_id,
            self._alias,
            self._dataset_name,
            self._class_name,
            self._master_ee_id,
            self._replica_ee_ids,
            LANG_PYTHON,
            self._is_read_only,
        )
        return object_md

    @metadata.setter
    def metadata(self, object_md):
        # self.__metadata = object_md
        self._object_id = object_md.id
        self._alias = object_md.alias_name
        self._dataset_name = object_md.dataset_name
        self._master_ee_id = object_md.master_ee_id
        self._replica_ee_ids = object_md.replica_ee_ids
        self._is_read_only = object_md.is_read_only

    def get_all_locations(self):
        """Return all the locations of this object."""
        return get_runtime().get_all_locations(self._object_id)

    # TODO: This function is redundant. Change it to get_random_backend(self), and implement it
    def get_location(self):
        """Return a single (random) location of this object."""
        # return get_runtime().get_location(self.__dclay_instance_extradata.object_id)
        return self._master_ee_id

    #################################
    # Extradata getters and setters #
    #################################

    # DEPRECATED
    def get_original_object_id(self):
        # return self.__dclay_instance_extradata.original_object_id
        return self._object_id

    # DEPRECATED
    def set_original_object_id(self, new_original_object_id):
        # self.__dclay_instance_extradata.original_object_id = new_original_object_id
        pass

    # DEPRECATED
    def get_root_location(self):
        # return self.__dclay_instance_extradata.root_location
        return self._master_ee_id

    # DEPRECATED
    def set_root_location(self, new_root_location):
        # self.__dclay_instance_extradata.root_location = new_root_location
        pass

    # DEPRECATED
    def get_origin_location(self):
        # return self.__dclay_instance_extradata.origin_location
        return self._master_ee_id

    # DEPRECATED
    def set_origin_location(self, new_origin_location):
        # self.__dclay_instance_extradata.origin_location = new_origin_location
        pass

    def add_replica_location(self, new_replica_location):
        replica_locations = self._replica_ee_ids
        if replica_locations is None:
            replica_locations = list()
            self._replica_ee_ids = replica_locations
        replica_locations.append(new_replica_location)

    def remove_replica_location(self, old_replica_location):
        replica_locations = self._replica_ee_ids
        replica_locations.remove(old_replica_location)

    def clear_replica_locations(self):
        replica_locations = self._replica_ee_ids
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
        from dataclay.DataClayObjProperties import DCLAY_SETTER_PREFIX

        return get_runtime().synchronize(self, DCLAY_SETTER_PREFIX + field_name, value)

    def session_detach(self):
        """
        Detach object from session, i.e. remove reference from current session provided to current object,
            'dear garbage-collector, the current session is not using this object anymore'
        """
        get_runtime().detach_object_from_session(self._object_id, self._master_ee_id)

    #################
    # Serialization #
    #################

    def serialize(
        self,
        io_file,
        ignore_user_types,
        iface_bitmaps,
        cur_serialized_objs,
        pending_objs,
        reference_counting,
    ):
        raise
        # Reference counting information
        # First integer represent the position in the buffer in which
        # reference counting starts. This is done to avoid "holding"
        # unnecessary information during a store or update in disk.

        # in new serialization, this will be done through padding
        # TODO: use padding instead once new serialization is implemented
        IntegerWrapper().write(io_file, 0)

        cur_master_loc = self._master_ee_id
        if cur_master_loc is not None:
            StringWrapper().write(io_file, str(cur_master_loc))
        else:
            StringWrapper().write(io_file, str("x"))

        if hasattr(self, "__getstate__"):
            # The object has a user-defined serialization method.
            # Use that
            last_loaded_flag = self._is_loaded
            last_persistent_flag = self._is_persistent

            self._is_loaded = True
            self._is_persistent = False

            # Use pickle to the result of the serialization
            state = pickle.dumps(self.__getstate__())

            # Leave the previous value, probably False & True`
            self._is_loaded = last_loaded_flag
            self._is_persistent = last_persistent_flag

            StringWrapper(mode="binary").write(io_file, state)

        else:
            # Regular dataClay provided serialization
            # Get the list of properties, making sure it is sorted
            properties = sorted(
                self.get_class_extradata().properties.values(), key=attrgetter("position")
            )

            logger.verbose("Serializing list of properties: %s", properties)

            for p in properties:

                try:
                    value = object.__getattribute__(self, "%s%s" % (DCLAY_PROPERTY_PREFIX, p.name))
                except AttributeError:
                    value = None

                logger.verbose("Serializing property %s", p.name)

                if value is None:
                    BooleanWrapper().write(io_file, False)
                else:
                    if isinstance(p.type, UserType):
                        if not ignore_user_types:
                            BooleanWrapper().write(io_file, True)
                            SerializationLibUtilsSingleton.serialize_association(
                                io_file,
                                value,
                                cur_serialized_objs,
                                pending_objs,
                                reference_counting,
                            )
                        else:
                            BooleanWrapper().write(io_file, False)
                    else:
                        BooleanWrapper().write(io_file, True)
                        pck = pickle.Pickler(io_file, protocol=-1)
                        pck.persistent_id = PersistentIdPicklerHelper(
                            cur_serialized_objs, pending_objs, reference_counting
                        )
                        pck.dump(value)

        # Reference counting
        # TODO: this should be removed in new serialization
        # TODO: (by using paddings to directly access reference counters inside metadata)

        cur_stream_pos = io_file.tell()
        io_file.seek(0)
        IntegerWrapper().write(io_file, cur_stream_pos)
        io_file.seek(cur_stream_pos)
        reference_counting.serialize_reference_counting(self, io_file)

    def deserialize(self, io_file, iface_bitmaps, metadata, cur_deserialized_python_objs):
        """Reciprocal to serialize."""
        logger.verbose("Deserializing object %s", str(self._object_id))

        # Put slow debugging info inside here:
        #
        # NOTE: new implementation of ExecutionGateway assert is not needed and wrong
        # if logger.isEnabledFor(DEBUG):
        #     klass = self.__class__
        #     logger.debug("Deserializing instance %r from class %s",
        #                  self, klass.__name__)
        #     logger.debug("The previous class is from module %s, in file %s",
        #                  klass.__module__, inspect.getfile(klass))
        #     logger.debug("The class extradata is:\n%s", klass._dclay_class_extradata)
        #     assert klass._dclay_class_extradata == self._dclay_class_extradata
        #
        # LOADED FLAG = TRUE only once deserialization is finished to avoid concurrent problems!
        # # This may be due to race conditions. It may need to do some extra locking
        # if self.__dclay_instance_extradata.loaded_flag:
        #     logger.debug("Loaded Flag is True")
        # else:
        #     self.__dclay_instance_extradata.loaded_flag = True

        raise

        """ reference counting """
        """ discard padding """
        IntegerWrapper().read(io_file)

        """ deserialize master_location """
        des_master_loc_str = StringWrapper().read(io_file)
        if des_master_loc_str == "x":
            self._master_ee_id = None
        else:
            self._master_ee_id = uuid.UUID(des_master_loc_str)

        if hasattr(self, "__setstate__"):
            # The object has a user-defined deserialization method.

            state = pickle.loads(StringWrapper(mode="binary").read(io_file))
            self.__setstate__(state)

        else:
            # Regular dataClay provided deserialization

            # Start by getting the properties
            properties = sorted(
                self.get_class_extradata().properties.values(), key=attrgetter("position")
            )

            logger.trace("Tell io_file before loop: %s", io_file.tell())
            logger.verbose("Deserializing list of properties: %s", properties)

            for p in properties:

                logger.trace("Tell io_file in loop: %s", io_file.tell())
                not_null = BooleanWrapper().read(io_file)
                value = None
                if not_null:
                    logger.debug("Not null property %s", p.name)
                    if isinstance(p.type, UserType):
                        try:
                            logger.debug("Property %s is an association", p.name)
                            value = DeserializationLibUtilsSingleton.deserialize_association(
                                io_file,
                                iface_bitmaps,
                                metadata,
                                cur_deserialized_python_objs,
                                get_runtime(),
                            )
                        except KeyError as e:
                            logger.error("Failed to deserialize association", exc_info=True)
                    else:
                        try:
                            upck = pickle.Unpickler(io_file)
                            upck.persistent_load = PersistentLoadPicklerHelper(
                                metadata, cur_deserialized_python_objs, get_runtime()
                            )
                            value = upck.load()
                        except:
                            traceback.print_exc()

                # FIXME: setting value calls __str__ that can cause a remote call!
                # logger.debug("Setting value %s for property %s", value, p.name)

                object.__setattr__(self, "%s%s" % (DCLAY_PROPERTY_PREFIX, p.name), value)

        """ reference counting bytes here """
        """ TODO: discard bytes? """

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

        if not self._is_persistent:
            logger.debug("Pickling of object is causing a make_persistent")
            self.make_persistent()

        return _get_object_by_id_helper, (
            self._object_id,
            self._class,  # self.get_class_extradata().class_id,
            self._master_ee_id,
        )

    def __repr__(self):

        if self._is_persistent:
            return "<%s instance with ObjectID=%s>" % (
                self._class_name,
                self._object_id,
            )
        else:
            return "<%s volatile instance with ObjectID=%s>" % (
                self._class_name,
                self._object_id,
            )

    def __eq__(self, other):
        if not isinstance(other, DataClayObject):
            return False

        if not self._is_persistent or not other._is_persistent:
            return False

        return self._object_id and other._object_id and self._object_id == other._object_id

    # FIXME: Think another solution, the user may want to override the method
    def __hash__(self):
        return hash(self._object_id)

    @dclayMethod(
        obj="anything", property_name="str", value="anything", beforeUpdate="str", afterUpdate="str"
    )
    def __setUpdate__(self, obj, property_name, value, beforeUpdate, afterUpdate):
        if beforeUpdate is not None:
            getattr(self, beforeUpdate)(property_name, value)
        object.__setattr__(obj, "%s%s" % ("_dataclay_property_", property_name), value)
        if afterUpdate is not None:
            getattr(self, afterUpdate)(property_name, value)
