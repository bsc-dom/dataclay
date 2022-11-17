"""Management of Python Classes.

This module is responsible of management of the Class Objects. A central Python
Metaclass is responsible of Class (not object) instantiation.

Note that this managers also includes most serialization/deserialization code
related to classes and function call parameters.
"""

import functools
import logging
import pickle
import traceback
import typing
import uuid
from uuid import UUID

from dataclay_common.managers.object_manager import ObjectMetadata
from dataclay_common.protos.common_messages_pb2 import LANG_PYTHON
from opentelemetry import trace

from dataclay.runtime import get_runtime

DCLAY_PROPERTY_PREFIX = "_dc_property_"


tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)


def activemethod(func):
    """Decorator for DataClayObject active methods"""

    @functools.wraps(func)
    def wrapper_activemethod(self, *args, **kwargs):
        logger.verbose(f"Calling function {func.__name__}")
        try:
            # If the object is not persistent executes the method locally,
            # else, executes the method within the execution environment
            if (
                (get_runtime().is_exec_env() and self._dc_is_loaded)
                or (get_runtime().is_client() and not self._dc_is_persistent)
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


class DataClayProperty:

    __slots__ = "property_name", "dc_property_name"

    def __init__(self, property_name):
        self.property_name = property_name
        self.dc_property_name = DCLAY_PROPERTY_PREFIX + property_name

    def __get__(self, instance, owner):
        is_exec_env = get_runtime().is_exec_env()

        if (is_exec_env and instance._dc_is_loaded) or (
            not is_exec_env and not instance._dc_is_persistent
        ):
            try:
                instance._dc_is_dirty = True
                # set dirty = true for language types like lists, dicts, that are get and modified. TODO: improve this.
                return getattr(instance, self.dc_property_name)
            except AttributeError as e:
                logger.warning(
                    f"Received AttributeError while accessing property {self.property_name} on instance {instance}"
                )
                logger.debug(f"Internal dictionary of the intance: {instance.__dict__}")
                e.args = (e.args[0].replace(self.dc_property_name, self.property_name),)
                raise e
        else:
            return get_runtime().call_active_method(
                instance, "__getattribute__", (self.property_name,), {}
            )

    def __set__(self, instance, value):
        """Setter for the dataClay property

        See the __get__ method for the basic behavioural explanation.
        """
        logger.debug(f"Calling setter for property {self.property_name}")

        is_exec_env = get_runtime().is_exec_env()
        if (is_exec_env and instance._dc_is_loaded) or (
            not is_exec_env and not instance._dc_is_persistent
        ):
            setattr(instance, self.dc_property_name, value)
            if is_exec_env:
                instance._dc_is_dirty = True
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
    _dc_alias: str
    _dc_dataset_name: str
    _dc_class: type
    _dc_class_name: str
    _dc_is_persistent: bool
    _dc_master_ee_id: UUID
    _dc_replica_ee_ids: list[UUID]
    _dc_language: int
    _dc_is_read_only: bool
    _dc_is_dirty: bool
    _dc_is_pending_to_register: bool
    _dc_is_loaded: bool
    _dc_owner_session_id: UUID

    def __init_subclass__(cls) -> None:
        """Defines a @property for each annotatted attribute"""
        for property_name in typing.get_type_hints(cls):
            if not property_name.startswith("_dc_"):
                setattr(cls, property_name, DataClayProperty(property_name))

    def __new__(cls, *args, **kwargs):
        logger.debug(f"Crated new dataclay object with args={args}, kwargs={kwargs}")
        obj = super().__new__(cls)
        obj.initialize_object()
        return obj

    @classmethod
    def new_volatile(cls, **kwargs):
        obj = super().__new__(cls)

        new_dict = kwargs

        if get_runtime().is_exec_env():
            # *** Execution Environment flags
            obj._dc_is_pending_to_register = True
            new_dict["_dc_is_persistent"] = True  # All objects in the EE are persistent
            new_dict["_dc_is_loaded"] = True
            new_dict["_dc_is_pending_to_register"] = True
            new_dict["_dc_master_ee_id"] = get_runtime().get_hint()  # It should be in kwargs

        obj.initialize_object(**new_dict)
        return obj

    @classmethod
    def new_persistent(cls, object_id, master_ee_id):
        obj = super().__new__(cls)

        new_dict = {}
        new_dict["_dc_is_persistent"] = True
        new_dict["_dc_id"] = object_id
        new_dict["_dc_master_ee_id"] = master_ee_id

        if get_runtime().is_exec_env():
            # *** Execution Environment flags
            # by default, loaded = true for volatiles created inside executions
            # this function (initialize as persistent) is used for objects being
            # deserialized and therefore they might be unloaded
            # same happens for pending to register flag.
            new_dict["_dc_is_loaded"] = False
            new_dict["_dc_is_pending_to_register"] = False

        obj.initialize_object(**new_dict)
        return obj

    def initialize_object(self, **kwargs):
        """Initializes the object"""

        # Populate default internal fields
        self._dc_id = uuid.uuid4()
        self._dc_alias = None
        self._dc_dataset_name = get_runtime().session.dataset_name
        self._dc_class = self.__class__
        self._dc_class_name = self.__class__.__module__ + "." + self.__class__.__name__
        self._dc_is_persistent = False
        self._dc_master_ee_id = (
            get_runtime().get_hint()
        )  # May be replaced if instantiating a thing object from different ee
        self._dc_replica_ee_ids = []
        self._dc_language = LANG_PYTHON
        self._dc_is_read_only = False
        self._dc_is_dirty = False
        self._dc_is_pending_to_register = False
        self._dc_is_loaded = True
        self._dc_owner_session_id = (
            get_runtime().session.id
        )  # May be removed to instantiate dc object without init()

        # Update object dict with custome kwargs
        self.__dict__.update(kwargs)

        # Add instance to heap
        get_runtime().add_to_heap(self)

    @property
    def dataclay_id(self):
        return self._dc_id

    @property
    def dataset(self):
        return self._dc_dataset_name

    @property
    def metadata(self):
        return ObjectMetadata(
            self._dc_id,
            self._dc_alias,
            self._dc_dataset_name,
            self._dc_class_name,
            self._dc_master_ee_id,
            self._dc_replica_ee_ids,
            self._dc_language,
            self._dc_is_read_only,
        )

    @metadata.setter
    def metadata(self, object_md):
        self._dc_id = object_md.id
        self._dc_alias = object_md.alias_name
        self._dc_dataset_name = object_md.dataset_name
        self._dc_master_ee_id = object_md.master_ee_id
        self._dc_replica_ee_ids = object_md.replica_ee_ids
        self._dc_is_read_only = object_md.is_read_only

    ################
    # TODO: REFACTOR
    ################

    def new_replica(self, backend_id=None, recursive=True):
        return get_runtime().new_replica(
            self._dc_id, self._dc_master_ee_id, backend_id, None, recursive
        )

    def new_version(self, backend_id=None, recursive=True):
        return get_runtime().new_version(
            self._dc_id,
            self._dc_master_ee_id,
            self._dc_class_name,
            self._dc_dataset_name,
            backend_id,
            None,
            recursive,
        )

    def consolidate_version(self):
        """Consolidate: copy contents of current version object to original object"""
        return get_runtime().consolidate_version(self._dc_id, self._dc_master_ee_id)

    def set_all(self, from_object):
        raise ("set_all need to be refactored")
        properties = sorted(
            self.get_class_extradata().properties.values(), key=attrgetter("position")
        )

        logger.verbose("Set all properties from object %s", from_object._dc_id)

        for p in properties:
            value = getattr(from_object, p.name)
            setattr(self, p.name, value)

    ################
    ################
    ################

    def make_persistent(self, alias=None, backend_id=None, recursive=True):

        with tracer.start_as_current_span(
            "make_persistent",
            attributes={"alias": str(alias), "backend_id": str(backend_id), "recursive": recursive},
        ):
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
        if self._dc_is_persistent:

            return "%s:%s:%s" % (
                self._dc_id,
                self._dc_master_ee_id,
                self._dc_class_name,
            )
        else:
            return None

    @classmethod
    def get_object_by_id(cls, object_id: UUID, master_ee_id: UUID = None):
        return get_runtime().get_object_by_id(object_id, cls, master_ee_id)

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

    def get_all_locations(self):
        """Return all the locations of this object."""
        return get_runtime().get_all_locations(self._dc_id)

    # TODO: Implement it?
    def get_random_backend(self):
        pass

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
        return self._dc_master_ee_id

    # DEPRECATED
    def set_root_location(self, new_root_location):
        # self.__dclay_instance_extradata.root_location = new_root_location
        pass

    # DEPRECATED
    def get_origin_location(self):
        # return self.__dclay_instance_extradata.origin_location
        return self._dc_master_ee_id

    # DEPRECATED
    def set_origin_location(self, new_origin_location):
        # self.__dclay_instance_extradata.origin_location = new_origin_location
        pass

    def add_replica_location(self, new_replica_location):
        replica_locations = self._dc_replica_ee_ids
        if replica_locations is None:
            replica_locations = list()
            self._dc_replica_ee_ids = replica_locations
        replica_locations.append(new_replica_location)

    def remove_replica_location(self, old_replica_location):
        replica_locations = self._dc_replica_ee_ids
        replica_locations.remove(old_replica_location)

    def clear_replica_locations(self):
        replica_locations = self._dc_replica_ee_ids
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
        get_runtime().detach_object_from_session(self._dc_id, self._dc_master_ee_id)

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

        cur_master_loc = self._dc_master_ee_id
        if cur_master_loc is not None:
            StringWrapper().write(io_file, str(cur_master_loc))
        else:
            StringWrapper().write(io_file, str("x"))

        if hasattr(self, "__getstate__"):
            # The object has a user-defined serialization method.
            # Use that
            last_loaded_flag = self._dc_is_loaded
            last_persistent_flag = self._dc_is_persistent

            self._dc_is_loaded = True
            self._dc_is_persistent = False

            # Use pickle to the result of the serialization
            state = pickle.dumps(self.__getstate__())

            # Leave the previous value, probably False & True`
            self._dc_is_loaded = last_loaded_flag
            self._dc_is_persistent = last_persistent_flag

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
        logger.verbose("Deserializing object %s", str(self._dc_id))

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
            self._dc_master_ee_id = None
        else:
            self._dc_master_ee_id = UUID(des_master_loc_str)

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

        if not self._dc_is_persistent:
            logger.debug("Pickling of object is causing a make_persistent")
            self.make_persistent()

        return self.get_object_by_id, (
            self._dc_id,
            self._dc_master_ee_id,
        )

    def __repr__(self):

        if self._dc_is_persistent:
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

        if not self._dc_is_persistent or not other._dc_is_persistent:
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
