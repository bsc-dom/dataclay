"""Management of Python Classes.

This module is responsible of management of the Class Objects. A central Python
Metaclass is responsible of Class (not object) instantiation.

Note that this managers also includes most serialization/deserialization code
related to classes and function call parameters.
"""
import inspect
import logging
import pickle
import re
import traceback
import uuid
from operator import attrgetter

from dataclay_common.managers.object_manager import ObjectMetadata
from dataclay_common.protos.common_messages_pb2 import LANG_PYTHON

from dataclay.commonruntime.ExecutionGateway import (
    ExecutionGateway,
    class_extradata_cache_client,
    class_extradata_cache_exec_env,
)
from dataclay.commonruntime.Runtime import get_runtime
from dataclay.DataClayObjectExtraData import DataClayClassExtraData, DataClayInstanceExtraData
from dataclay.DataClayObjMethods import dclayMethod
from dataclay.DataClayObjProperties import (
    DCLAY_PROPERTY_PREFIX,
    DynamicProperty,
    PreprocessedProperty,
    ReplicatedDynamicProperty,
)
from dataclay.exceptions.exceptions import DataClayException, ImproperlyConfigured
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
__author__ = "Alex Barcelo <alex.barcelo@bsc.es>"
__copyright__ = "2016 Barcelona Supercomputing Center (BSC-CNS)"

logger = logging.getLogger(__name__)

# For efficiency purposes compile the folowing regular expressions:
# (they return a tuple of two elements)
re_property = re.compile(
    r"(?:^\s*@dclayReplication\s*\(\s*(before|after)Update\s*=\s*'([^']+)'(?:,\s(before|after)Update='([^']+)')?(?:,\sinMaster='(True|False)')?\s*\)\n)?^\s*@ClassField\s+([\w.]+)[ \t]+([\w.\[\]<> ,]+)",
    re.MULTILINE,
)
re_import = re.compile(r"^\s*@d[cC]layImport(?P<from_mode>From)?\s+(?P<import>.+)$", re.MULTILINE)


def _get_object_by_id_helper(object_id, class_id, hint):
    """Helper method which can be pickled and used by DataClayObject.__reduce__"""
    return get_runtime().get_object_by_id(object_id, class_id, hint)


class DataClayObject(object, metaclass=ExecutionGateway):
    """Main class for Persistent Objects.

    Objects that has to be made persistent should derive this class (either
    directly, through the StorageObject alias, or through a derived class).
    """

    # Extradata of the object. Private field.
    __dclay_instance_extradata = None

    def initialize_object(self, deserializing=False, **kwargs):
        """Initializes the object"""
        self._populate_internal_fields(**kwargs)
        get_runtime().add_to_heap(self)

        if not deserializing:
            """object created during executions is volatile."""
            self.initialize_object_as_volatile()

    def initialize_object_as_persistent(self):
        """Initializes the object as a persistent

        Flags for "persistent" state might be different in EE and client.
        """
        # TODO: improve this using an specialization (dgasull)
        self.set_persistent(True)

        if get_runtime().is_exec_env():
            # *** Execution Environment flags
            # by default, loaded = true for volatiles created inside executions
            # this function (initialize as persistent) is used for objects being
            # deserialized and therefore they might be unloaded
            # same happens for pending to register flag.
            self.set_loaded(False)
            self.set_pending_to_register(False)

    def initialize_object_as_volatile(self):
        """Initialize object with state 'volatile' with proper flags.

        Usually, volatile state is created by a stub, app, exec, class,..
        See same function in DataClayExecutionObject for a different initialization.
        This design is intended to be clear with object state.
        """
        # TODO: improve this using an specialization (dgasull)
        if get_runtime().is_exec_env():
            # *** Execution Environment flags
            self.set_persistent(True)  # All objects in the EE are persistent
            self.set_loaded(True)
            self.set_pending_to_register(True)
            self.set_hint(get_runtime().get_hint())
            self.set_owner_session_id(get_runtime().session.id)

    def _populate_internal_fields(self, **kwargs):
        logger.debug(f"Populating internal fields for the class. Provided kwargs: {kwargs}")

        # My test
        # self.__metadata = ObjectMetadata(
        #     id=uuid.uuid4(),
        #     alias_name=None,
        #     dataset_name=get_runtime().session.dataset_name,
        #     class_id=self.get_class_extradata().class_id,
        #     master_ee_id=get_runtime().get_hint(),
        #     replica_ee_ids=None,
        #     language=LANG_PYTHON,
        #     is_read_only=False,
        # )

        # Mix default values with the provided ones through kwargs
        fields = {
            "persistent_flag": False,
            "object_id": uuid.uuid4(),
            "dataset_name": get_runtime().session.dataset_name,
            "replica_locations": [],
            "is_read_only": False,
            "pending_to_register_flag": False,
            "dirty_flag": False,
            "memory_pinned": False,
            "loaded_flag": True,
        }
        fields.update(kwargs)

        # Store some extradata in the class
        instance_dict = object.__getattribute__(self, "__dict__")
        instance_dict["_DataClayObject__dclay_instance_extradata"] = DataClayInstanceExtraData(
            **fields
        )

        # TODO: get_class_extradata function is adding DynamicProperties to class (not to instance!) so it is needed
        # to be called. Please, use a better function for that.
        instance_dict["_dclay_class_extradata"] = self.get_class_extradata()

    @classmethod
    def get_class_extradata(cls):
        classname = cls.__name__
        module_name = cls.__module__
        full_name = module_name + "." + classname

        # Check if class extradata is in cache.
        if get_runtime().is_client():
            dc_ced = class_extradata_cache_client.get(full_name)
        else:
            dc_ced = class_extradata_cache_exec_env.get(full_name)

        if dc_ced is not None:
            logger.debug("Found class %s extradata in cache" % full_name)
            return dc_ced

        logger.verbose("Proceeding to prepare the class `%s` from the ExecutionGateway", full_name)
        logger.debug(
            "The Runtime Type is: %s",
            "client" if get_runtime().is_client() else "not client",
        )

        dc_ced = DataClayClassExtraData(
            full_name=full_name,
            classname=classname,
            namespace=module_name.split(".", 1)[0],
            properties=dict(),
            imports=list(),
        )

        if get_runtime().is_client():
            class_stubinfo = None

            try:
                all_classes = load_babel_data()

                for c in all_classes:
                    if "%s.%s" % (c.namespace, c.className) == full_name:
                        class_stubinfo = c
                        break
            except ImproperlyConfigured:
                pass

            if class_stubinfo is None:
                # Either ImproperlyConfigured (not initialized) or class not found:
                # assuming non-registered class

                # Let's navigate all the heritance, and aggregate all the information that can be found.
                # FIXME: This code is NOT considering the scenario in which a class is extending an already registered one.
                # FIXME: Behaviour when an attribute is defined in more than one class is not tested nor defined right now.
                for current_cls in inspect.getmro(cls):
                    # Ignore `object` and also ignore DataClayObject itself
                    if current_cls in [object, DataClayObject]:
                        continue

                    # Prepare properties from the docstring
                    doc = current_cls.__doc__  # If no documentation, consider an empty string
                    if doc is None:
                        doc = ""
                    property_pos = 0

                    for m in re_property.finditer(doc):
                        # declaration in the form [ 'before|after', 'method', 'before|after', 'method', 'name', 'type' ]
                        declaration = m.groups()
                        prop_name = declaration[-2]
                        prop_type = declaration[-1]

                        beforeUpdate = (
                            declaration[1]
                            if declaration[0] == "before"
                            else declaration[3]
                            if declaration[2] == "before"
                            else None
                        )

                        afterUpdate = (
                            declaration[1]
                            if declaration[0] == "after"
                            else declaration[3]
                            if declaration[2] == "after"
                            else None
                        )

                        inMaster = declaration[4] == "True"

                        current_type = Type.build_from_docstring(prop_type)

                        logger.trace(
                            "Property `%s` (with type signature `%s`) ready to go",
                            prop_name,
                            current_type.signature,
                        )

                        dc_ced.properties[prop_name] = PreprocessedProperty(
                            name=prop_name,
                            position=property_pos,
                            type=current_type,
                            beforeUpdate=beforeUpdate,
                            afterUpdate=afterUpdate,
                            inMaster=inMaster,
                        )

                        # Keep the position tracking (required for other languages compatibility)
                        property_pos += 1

                        # Prepare the `property` magic --this one without getter and setter ids
                        # dct[prop_name] = DynamicProperty(prop_name)
                        setattr(cls, prop_name, DynamicProperty(prop_name))
                        # WARNING: This is done in `cls` and not in `current_cls` deliberately.

                    for m in re_import.finditer(doc):
                        gd = m.groupdict()

                        if gd["from_mode"]:
                            import_str = "from %s\n" % gd["import"]
                        else:
                            import_str = "import %s\n" % gd["import"]

                        dc_ced.imports.append(import_str)

            else:
                logger.debug("Loading a class with babel_data information")

                dc_ced.class_id = class_stubinfo.classID
                dc_ced.stub_info = class_stubinfo

                # WIP WORK IN PROGRESS (because all that is for the ancient StubInfo, not the new one)

                # Prepare the `property` magic --in addition to prepare the properties dictionary too
                for i, prop_name in enumerate(dc_ced.stub_info.propertyListWithNulls):

                    if prop_name is None:
                        continue

                    prop_info = class_stubinfo.properties[prop_name]
                    if prop_info.beforeUpdate is not None or prop_info.afterUpdate is not None:
                        setattr(
                            cls,
                            prop_name,
                            ReplicatedDynamicProperty(
                                prop_name,
                                prop_info.beforeUpdate,
                                prop_info.afterUpdate,
                                prop_info.inMaster,
                            ),
                        )

                    else:
                        # dct[prop_name] = DynamicProperty(prop_name)
                        setattr(cls, prop_name, DynamicProperty(prop_name))

                    dc_ced.properties[prop_name] = PreprocessedProperty(
                        name=prop_name,
                        position=i,
                        type=prop_info.propertyType,
                        beforeUpdate=prop_info.beforeUpdate,
                        afterUpdate=prop_info.afterUpdate,
                        inMaster=prop_info.inMaster,
                    )

        elif get_runtime().is_exec_env():
            logger.verbose(
                "Seems that we are a DataService, proceeding to load class %s", dc_ced.full_name
            )
            namespace_in_classname, dclay_classname = dc_ced.full_name.split(".", 1)
            if namespace_in_classname != dc_ced.namespace:
                raise DataClayException(
                    "Namespace in ClassName: %s is different from one in ClassExtraData: %s",
                    namespace_in_classname,
                    dc_ced.namespace,
                )
            mc = load_metaclass(dc_ced.namespace, dclay_classname)
            dc_ced.metaclass_container = mc
            dc_ced.class_id = mc.dataClayID

            # Prepare the `property` magic --in addition to prepare the properties dictionary too
            for prop_info in dc_ced.metaclass_container.properties:
                if prop_info.beforeUpdate is not None or prop_info.afterUpdate is not None:
                    setattr(
                        cls,
                        prop_info.name,
                        ReplicatedDynamicProperty(
                            prop_info.name,
                            prop_info.beforeUpdate,
                            prop_info.afterUpdate,
                            prop_info.inMaster,
                        ),
                    )
                else:
                    setattr(cls, prop_info.name, DynamicProperty(prop_info.name))

                dc_ced.properties[prop_info.name] = PreprocessedProperty(
                    name=prop_info.name,
                    position=prop_info.position,
                    type=prop_info.type,
                    beforeUpdate=prop_info.beforeUpdate,
                    afterUpdate=prop_info.afterUpdate,
                    inMaster=prop_info.inMaster,
                )
        else:
            raise RuntimeError(f"Could not recognize Runtime Type {type(get_runtime()).__name__}")

        # Update class extradata cache.
        if get_runtime().is_client():
            class_extradata_cache_client[full_name] = dc_ced
        else:
            class_extradata_cache_exec_env[full_name] = dc_ced

        return dc_ced

    def new_replica(self, backend_id=None, recursive=True):
        return get_runtime().new_replica(
            self.get_object_id(), self.get_hint(), backend_id, None, recursive
        )

    def new_version(self, backend_id=None, recursive=True):
        return get_runtime().new_version(
            self.get_object_id(),
            self.get_hint(),
            self.get_class_id(),
            self.get_dataset_name(),
            backend_id,
            None,
            recursive,
        )

    def consolidate_version(self):
        """Consolidate: copy contents of current version object to original object"""
        return get_runtime().consolidate_version(self.get_object_id(), self.get_hint())

    def make_persistent(self, alias=None, backend_id=None, recursive=True):
        if alias == "":
            raise AttributeError("Alias cannot be empty")
        get_runtime().make_persistent(self, alias=alias, backend_id=backend_id, recursive=recursive)

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
        properties = sorted(
            self.get_class_extradata().properties.values(), key=attrgetter("position")
        )

        logger.verbose("Set all properties from object %s", from_object.get_object_id())

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
        if self.is_persistent():
            hint = self.__dclay_instance_extradata.execenv_id or ""

            return "%s:%s:%s" % (
                self.__dclay_instance_extradata.object_id,
                hint,
                self.get_class_extradata().class_id,
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
            self.get_object_id(),
            self.get_alias(),
            self.get_dataset_name(),
            self.get_class_id(),
            self.get_hint(),
            self.get_replica_locations(),
            LANG_PYTHON,
            self.is_read_only(),
        )
        return object_md

    @metadata.setter
    def metadata(self, object_md):
        # self.__metadata = object_md
        self.set_object_id(object_md.id)
        self.set_alias(object_md.alias_name)
        self.set_dataset_name(object_md.dataset_name)
        self.set_hint(object_md.master_ee_id)
        self.set_replica_locations(object_md.replica_ee_ids)
        self.set_read_only(object_md.is_read_only)

    def get_all_locations(self):
        """Return all the locations of this object."""
        return get_runtime().get_all_locations(self.__dclay_instance_extradata.object_id)

    # TODO: This function is redundant. Change it to get_random_backend(self), and implement it
    def get_location(self):
        """Return a single (random) location of this object."""
        # return get_runtime().get_location(self.__dclay_instance_extradata.object_id)
        return self.get_hint()

    ##########################################
    # Metadata getters and setters #
    ##########################################

    def get_object_id(self):
        return self.__dclay_instance_extradata.object_id

    def set_object_id(self, new_object_id):
        self.__dclay_instance_extradata.object_id = new_object_id

    def get_alias(self):
        return self.__dclay_instance_extradata.alias

    def set_alias(self, new_alias):
        self.__dclay_instance_extradata.alias = new_alias

    # TODO: Rename hint to backend? or master_backend?
    def get_hint(self):
        return self.__dclay_instance_extradata.execenv_id

    # TODO: Rename hint to backend?
    def set_hint(self, new_hint):
        self.__dclay_instance_extradata.execenv_id = new_hint

    def is_read_only(self):
        return self.__dclay_instance_extradata.is_read_only

    def set_read_only(self, new_read_only):
        self.__dclay_instance_extradata.is_read_only = new_read_only

    def get_dataset_name(self):
        return self.__dclay_instance_extradata.dataset_name

    def set_dataset_name(self, new_dataset_name):
        self.__dclay_instance_extradata.dataset_name = new_dataset_name

    #################################
    # Extradata getters and setters #
    #################################

    def get_original_object_id(self):
        return self.__dclay_instance_extradata.original_object_id

    def set_original_object_id(self, new_original_object_id):
        self.__dclay_instance_extradata.original_object_id = new_original_object_id

    def get_root_location(self):
        return self.__dclay_instance_extradata.root_location

    def set_root_location(self, new_root_location):
        self.__dclay_instance_extradata.root_location = new_root_location

    def get_origin_location(self):
        return self.__dclay_instance_extradata.origin_location

    def set_origin_location(self, new_origin_location):
        self.__dclay_instance_extradata.origin_location = new_origin_location

    def get_replica_locations(self):
        return self.__dclay_instance_extradata.replica_locations

    def set_replica_locations(self, new_replica_locations):
        self.__dclay_instance_extradata.replica_locations = new_replica_locations

    def add_replica_location(self, new_replica_location):
        replica_locations = self.__dclay_instance_extradata.replica_locations
        if replica_locations is None:
            replica_locations = list()
            self.__dclay_instance_extradata.replica_locations = replica_locations
        replica_locations.append(new_replica_location)

    def remove_replica_location(self, old_replica_location):
        replica_locations = self.__dclay_instance_extradata.replica_locations
        replica_locations.remove(old_replica_location)

    def clear_replica_locations(self):
        replica_locations = self.__dclay_instance_extradata.replica_locations
        if replica_locations is not None:
            replica_locations.clear()

    def get_master_location(self):
        return self.__dclay_instance_extradata.master_location

    def set_master_location(self, eeid):
        self.__dclay_instance_extradata.master_location = eeid

    def get_memory_pinned(self):
        return self.__dclay_instance_extradata.memory_pinned

    def set_memory_pinned(self, new_memory_pinned):
        self.__dclay_instance_extradata.memory_pinned = new_memory_pinned

    def set_persistent(self, ispersistent):
        self.__dclay_instance_extradata.persistent_flag = ispersistent

    def set_loaded(self, isloaded):
        self.__dclay_instance_extradata.loaded_flag = isloaded

    def is_persistent(self):
        return self.__dclay_instance_extradata.persistent_flag

    def is_loaded(self):
        return self.__dclay_instance_extradata.loaded_flag

    def get_class_id(self):
        return self.get_class_extradata().class_id

    def get_owner_session_id(self):
        return self.__dclay_instance_extradata.owner_session_id

    def set_owner_session_id(self, the_owner_session_id):
        self.__dclay_instance_extradata.owner_session_id = the_owner_session_id

    def is_pending_to_register(self):
        return self.__dclay_instance_extradata.pending_to_register_flag

    def set_pending_to_register(self, pending_to_register):
        self.__dclay_instance_extradata.pending_to_register_flag = pending_to_register

    def is_dirty(self):
        return self.__dclay_instance_extradata.dirty_flag

    def set_dirty(self, dirty_value):
        self.__dclay_instance_extradata.dirty_flag = dirty_value

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
        get_runtime().detach_object_from_session(self.get_object_id(), self.get_hint())

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
        # Reference counting information
        # First integer represent the position in the buffer in which
        # reference counting starts. This is done to avoid "holding"
        # unnecessary information during a store or update in disk.

        # in new serialization, this will be done through padding
        # TODO: use padding instead once new serialization is implemented
        IntegerWrapper().write(io_file, 0)

        cur_master_loc = self.get_master_location()
        if cur_master_loc is not None:
            StringWrapper().write(io_file, str(cur_master_loc))
        else:
            StringWrapper().write(io_file, str("x"))

        if hasattr(self, "__getstate__"):
            # The object has a user-defined serialization method.
            # Use that
            dco_extradata = self.__dclay_instance_extradata
            last_loaded_flag = dco_extradata.loaded_flag
            last_persistent_flag = dco_extradata.persistent_flag
            dco_extradata.loaded_flag = True
            dco_extradata.persistent_flag = False

            # Use pickle to the result of the serialization
            state = pickle.dumps(self.__getstate__())

            # Leave the previous value, probably False & True`
            dco_extradata.loaded_flag = last_loaded_flag
            dco_extradata.persistent_flag = last_persistent_flag

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
        logger.verbose("Deserializing object %s", str(self.get_object_id()))

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

        """ reference counting """
        """ discard padding """
        IntegerWrapper().read(io_file)

        """ deserialize master_location """
        des_master_loc_str = StringWrapper().read(io_file)
        if des_master_loc_str == "x":
            self.__dclay_instance_extradata.master_location = None
        else:
            self.__dclay_instance_extradata.master_location = uuid.UUID(des_master_loc_str)

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
        logger.verbose("Proceeding to `__reduce__` (Pickle-related) on a DataClayObject")
        dco_extradata = self.__dclay_instance_extradata

        if not dco_extradata.persistent_flag:
            logger.verbose("Pickling of object is causing a make_persistent")
            self.make_persistent()

        return _get_object_by_id_helper, (
            self.get_object_id(),
            self.get_class_extradata().class_id,
            self.get_hint(),
        )

    def __repr__(self):
        dco_extradata = self.__dclay_instance_extradata
        dcc_extradata = self.get_class_extradata()

        if dco_extradata.persistent_flag:
            return "<%s (ClassID=%s) instance with ObjectID=%s>" % (
                dcc_extradata.classname,
                dcc_extradata.class_id,
                dco_extradata.object_id,
            )
        else:
            return "<%s (ClassID=%s) volatile instance with ObjectID=%s>" % (
                dcc_extradata.classname,
                dcc_extradata.class_id,
                dco_extradata.object_id,
            )

    def __eq__(self, other):
        if not isinstance(other, DataClayObject):
            return False

        self_extradata = self.__dclay_instance_extradata
        other_extradata = other.__dclay_instance_extradata

        if not self_extradata.persistent_flag or not other_extradata.persistent_flag:
            return False

        return (
            self_extradata.object_id
            and other_extradata.object_id
            and self_extradata.object_id == other_extradata.object_id
        )

    # FIXME: Think another solution, the user may want to override the method
    def __hash__(self):
        self_extradata = self.__dclay_instance_extradata
        return hash(self_extradata.object_id)

    @dclayMethod(
        obj="anything", property_name="str", value="anything", beforeUpdate="str", afterUpdate="str"
    )
    def __setUpdate__(self, obj, property_name, value, beforeUpdate, afterUpdate):
        if beforeUpdate is not None:
            getattr(self, beforeUpdate)(property_name, value)
        object.__setattr__(obj, "%s%s" % ("_dataclay_property_", property_name), value)
        if afterUpdate is not None:
            getattr(self, afterUpdate)(property_name, value)
