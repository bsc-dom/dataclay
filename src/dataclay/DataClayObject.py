"""Management of Python Classes.

This module is responsible of management of the Class Objects. A central Python
Metaclass is responsible of Class (not object) instantiation.

Note that this managers also includes most serialization/deserialization code
related to classes and function call parameters.
"""
import traceback
import logging
import copy
import re
from operator import attrgetter
from uuid import UUID

import six

if six.PY2:
    from cPickle import Pickler, Unpickler
elif six.PY3:
    from _pickle import Pickler, Unpickler
import uuid
from dataclay.DataClayObjMethods import dclayMethod
from dataclay.DataClayObjProperties import DCLAY_PROPERTY_PREFIX, PreprocessedProperty, DynamicProperty, \
    ReplicatedDynamicProperty
from dataclay.DataClayObjectExtraData import DataClayInstanceExtraData, DataClayClassExtraData
from dataclay.commonruntime.ExecutionGateway import ExecutionGateway, class_extradata_cache_client, \
    class_extradata_cache_exec_env
from dataclay.commonruntime.Runtime import getRuntime
from dataclay.commonruntime.RuntimeType import RuntimeType
from dataclay.serialization.lib.DeserializationLibUtils import DeserializationLibUtilsSingleton, PersistentLoadPicklerHelper
from dataclay.serialization.lib.SerializationLibUtils import SerializationLibUtilsSingleton, PersistentIdPicklerHelper
from dataclay.serialization.python.lang.BooleanWrapper import BooleanWrapper
from dataclay.serialization.python.lang.StringWrapper import StringWrapper
from dataclay.serialization.python.lang.IntegerWrapper import IntegerWrapper
from dataclay.serialization.python.lang.DCIDWrapper import DCIDWrapper
from dataclay.util.StubUtils import load_babel_data
from dataclay.util.classloaders.ClassLoader import load_metaclass
from dataclay.util.management.classmgr.Type import Type
from dataclay.util.management.classmgr.UserType import UserType
from dataclay.exceptions.exceptions import DataClayException, ImproperlyConfigured
import six

# Publicly show the dataClay method decorators
__author__ = 'Alex Barcelo <alex.barcelo@bsc.es>'
__copyright__ = '2016 Barcelona Supercomputing Center (BSC-CNS)'

logger = logging.getLogger(__name__)

# For efficiency purposes compile the folowing regular expressions:
# (they return a tuple of two elements)
re_property = re.compile(r"(?:^\s*@dclayReplication\s*\(\s*(before|after)Update\s*=\s*'([^']+)'(?:,\s(before|after)Update='([^']+)')?(?:,\sinMaster='(True|False)')?\s*\)\n)?^\s*@ClassField\s+([\w.]+)[ \t]+([\w.\[\]<> ,]+)", re.MULTILINE)
re_import = re.compile(r"^\s*@d[cC]layImport(?P<from_mode>From)?\s+(?P<import>.+)$", re.MULTILINE)


def _get_object_by_id_helper(object_id, class_id, hint):
    """Helper method which can be pickled and used by DataClayObject.__reduce__"""
    return getRuntime().get_object_by_id(object_id, class_id, hint)


@six.add_metaclass(ExecutionGateway)
class DataClayObject(object):
    """Main class for Persistent Objects.

    Objects that has to be made persistent should derive this class (either
    directly, through the StorageObject alias, or through a derived class).
    """

    # Extradata of the object. Private field.
    __dclay_instance_extradata = None
    
    def initialize_object(self, new_object_id=None):
        """ 
        @postcondition: Initialize the object 
        @param new_object_id: Object Id of the object
        """
        if new_object_id is not None:  # TODO: remove this if once ExecutionGateway is not initializing object id twice
            self.set_object_id(new_object_id)
        getRuntime().add_to_heap(self)
        
    def initialize_object_as_persistent(self):
        """
        @postcondition: object is initialized as a persistent object.
        Flags for "persistent" state might be different in EE and client.
        """
        # TODO: improve this using an specialization (dgasull) 
        if getRuntime().is_exec_env(): 
            # *** Execution Environment flags
            self.set_persistent(True)

            # by default, loaded = true for volatiles created inside executions
            # this function (initialize as persistent) is used for objects being
            # deserialized and therefore they might be unloaded
            # same happens for pending to register flag.
            self.set_loaded(False)
            self.set_pending_to_register(False)
            
        else: 
            # *** Client flags
            self.set_persistent(True)

    def initialize_object_as_volatile(self):
        """
        @postcondition: Initialize object with state 'volatile' with proper flags. Usually, volatile state is created by a stub, app, exec
        class,.. See same function in DataClayExecutionObject for a different initialization. This design is intended to be
        clear with object state.
        """
        # TODO: improve this using an specialization (dgasull) 
        if getRuntime().is_exec_env(): 
            # *** Execution Environment flags
            self.set_persistent(True)  # All objects in the EE are persistent
            self.set_loaded(True)
            self.set_pending_to_register(True)
            self.set_hint(getRuntime().get_hint())
            self.set_owner_session_id(getRuntime().get_session_id())
    
    @classmethod
    def get_class_extradata(cls):
        classname = cls.__name__
        module_name = cls.__module__
        full_name = "%s.%s" % (module_name, classname)

        # Check if class extradata is in cache.
        if getRuntime().current_type == RuntimeType.client:
            dc_ced = class_extradata_cache_client.get(full_name)
        else:
            dc_ced = class_extradata_cache_exec_env.get(full_name)

        if dc_ced is not None:
            return dc_ced

        logger.verbose('Proceeding to prepare the class `%s` from the ExecutionGateway',
                       full_name)
        logger.debug("The RuntimeType is: %s",
                     "client" if getRuntime().current_type == RuntimeType.client else "not client")

        dc_ced = DataClayClassExtraData(
            full_name=full_name,
            classname=classname,
            namespace=module_name.split('.', 1)[0],
            properties=dict(),
            imports=list(),
        )

        if getRuntime().current_type == RuntimeType.client:
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

                # Prepare properties from the docstring
                doc = cls.__doc__  # If no documentation, consider an empty string
                if doc is None:
                    doc = ""
                property_pos = 0

                for m in re_property.finditer(doc):
                    # declaration in the form [ 'before|after', 'method', 'before|after', 'method', 'name', 'type' ]
                    declaration = m.groups()
                    prop_name = declaration[-2]
                    prop_type = declaration[-1]

                    beforeUpdate = declaration[1] if declaration[0] == 'before' \
                        else declaration[3] if declaration[2] == 'before' else None

                    afterUpdate = declaration[1] if declaration[0] == 'after' \
                        else declaration[3] if declaration[2] == 'after' else None

                    inMaster = declaration[4] == 'True'

                    current_type = Type.build_from_docstring(prop_type)

                    logger.trace("Property `%s` (with type signature `%s`) ready to go",
                                 prop_name, current_type.signature)

                    dc_ced.properties[prop_name] = PreprocessedProperty(
                        name=prop_name,
                        position=property_pos,
                        type=current_type,
                        beforeUpdate=beforeUpdate,
                        afterUpdate=afterUpdate,
                        inMaster=inMaster)

                    # Keep the position tracking (required for other languages compatibility)
                    property_pos += 1

                    # Prepare the `property` magic --this one without getter and setter ids
                    # dct[prop_name] = DynamicProperty(prop_name)
                    setattr(cls, prop_name, DynamicProperty(prop_name))

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
                        setattr(cls, prop_name,
                                ReplicatedDynamicProperty(
                                    prop_name,
                                    prop_info.beforeUpdate,
                                    prop_info.afterUpdate,
                                    prop_info.inMaster
                                ))

                    else:
                        # dct[prop_name] = DynamicProperty(prop_name)
                        setattr(cls, prop_name, DynamicProperty(prop_name))

                    dc_ced.properties[prop_name] = PreprocessedProperty(name=prop_name, position=i,
                                                                        type=prop_info.propertyType,
                                                                        beforeUpdate=prop_info.beforeUpdate,
                                                                        afterUpdate=prop_info.afterUpdate,
                                                                        inMaster=prop_info.inMaster)

        elif getRuntime().current_type == RuntimeType.exe_env:
            logger.verbose("Seems that we are a DataService, proceeding to load class %s",
                           dc_ced.full_name)
            namespace_in_classname, dclay_classname = dc_ced.full_name.split(".", 1)
            if namespace_in_classname != dc_ced.namespace:
                raise DataClayException("Namespace in ClassName: %s is different from one in ClassExtraData: %s",
                                        namespace_in_classname, dc_ced.namespace)
            mc = load_metaclass(dc_ced.namespace, dclay_classname)
            dc_ced.metaclass_container = mc
            dc_ced.class_id = mc.dataClayID

            # Prepare the `property` magic --in addition to prepare the properties dictionary too
            for prop_info in dc_ced.metaclass_container.properties:
                if prop_info.beforeUpdate is not None or prop_info.afterUpdate is not None:
                    setattr(cls, prop_info.name,
                            ReplicatedDynamicProperty(
                                prop_info.name,
                                prop_info.beforeUpdate,
                                prop_info.afterUpdate,
                                prop_info.inMaster
                            ))
                else:
                    setattr(cls, prop_info.name, DynamicProperty(prop_info.name))

                dc_ced.properties[prop_info.name] = PreprocessedProperty(
                    name=prop_info.name,
                    position=prop_info.position,
                    type=prop_info.type,
                    beforeUpdate=prop_info.beforeUpdate,
                    afterUpdate=prop_info.afterUpdate,
                    inMaster=prop_info.inMaster)
        else:
            raise RuntimeError("Could not recognize RuntimeType %s", getRuntime().current_type)

        # Update class extradata cache.
        if getRuntime().current_type == RuntimeType.client:
            class_extradata_cache_client[full_name] = dc_ced
        else:
            class_extradata_cache_exec_env[full_name] = dc_ced

        return dc_ced

    def _populate_internal_fields(self, deserializing=False, **kwargs):
        logger.debug("Populating internal fields for the class. Provided kwargs: %s deserializing=%s", kwargs, str(deserializing))

        # Mix default values with the provided ones through kwargs
        fields = {
            "persistent_flag": False,
            "object_id": uuid.uuid4(),
            "dataset_id": None,
            "loaded_flag": True,
            "pending_to_register_flag": False,
            "dirty_flag": False,
            "memory_pinned": False,
        }
        fields.update(kwargs)

        # Store some extradata in the class
        instance_dict = object.__getattribute__(self, "__dict__")
        instance_dict["_DataClayObject__dclay_instance_extradata"] = DataClayInstanceExtraData(**fields)

        """
        TODO: get_class_extradata function is adding DynamicProperties to class (not to instance!) so it is needed 
        to be called. Please, use a better function for that. 
        """
        instance_dict["_dclay_class_extradata"] = self.get_class_extradata()
        
        # Initialize object
        self.initialize_object()
        if not deserializing: 
            """ object created during executions is volatile. """
            self.initialize_object_as_volatile()

    def get_location(self):
        """Return a single (random) location of this object."""
        return getRuntime().get_location(self.__dclay_instance_extradata.object_id)

    def get_master_location(self):
        """Return the uuid relative to the master location of this object."""
        return self.__dclay_instance_extradata.master_location

    def set_master_location(self, eeid):
        """Set the master location of this object."""
        if not isinstance(eeid, UUID):
            raise AttributeError("The master location should be the ExecutionEnvironmentID, "
                                 "instead we received: %s" % eeid)
        self.__dclay_instance_extradata.master_location = eeid
        
    def get_all_locations(self):
        """Return all the locations of this object."""
        return getRuntime().get_all_locations(self.__dclay_instance_extradata.object_id)
    
    def new_replica(self, backend_id=None, recursive=True):
        getRuntime().new_replica(self.get_object_id(), self.get_class_extradata().class_id,
                                 self.get_hint(), backend_id, recursive)

    def new_version(self, backend_id):
        return getRuntime().new_version(self.get_object_id(), self.get_class_extradata().class_id,
                                        self.get_hint(), backend_id)

    def consolidate_version(self, version_info):
        getRuntime().consolidate_version(version_info)

    def make_persistent(self, alias=None, backend_id=None, recursive=True):
        if alias is "":
            raise AttributeError('Alias cannot be empty')
        getRuntime().make_persistent(self, alias=alias, backend_id=backend_id, recursive=recursive)

    def get_execution_environments_info(self):
        return getRuntime().get_execution_environments_info()

    @classmethod
    def dc_clone_by_alias(cls, alias, recursive=False):
        o = cls.get_by_alias(alias)
        return o.dc_clone(recursive)

    def dc_clone(self, recursive=False):
        """
        @postcondition: Returns a non-persistent object as a copy of the current object
        @return: DataClayObject non-persistent instance
        """
        return getRuntime().get_copy_of_object(self, recursive)

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
            getRuntime().update_object(self, from_object)
            
    def dc_put(self, alias, backend_id=None, recursive=True):
        if alias is None or alias is "":
            raise AttributeError('Alias cannot be null or empty')
        getRuntime().make_persistent(self, alias=alias, backend_id=backend_id, recursive=recursive)
            
    def set_all(self, from_object):
        properties = sorted(self.get_class_extradata().properties.values(),
                key=attrgetter('position'))

        logger.verbose("Set all properties from object %s", from_object.get_object_id())

        for p in properties:
            value = getattr(from_object, p.name)
            setattr(self, p.name, value)

    def get_object_id(self):
        """
        @postcondition: Return object id of the object
        @return Object id
        """
        return self.__dclay_instance_extradata.object_id
    
    def set_object_id(self, new_object_id):
        """
        @postcondition: Set object id of the object
        @param new_object_id: object id
        """
        self.__dclay_instance_extradata.object_id = new_object_id

    def get_memory_pinned(self):
        """
        @postcondition: Return the memory pinned flag of the object
        @return Object id
        """
        return self.__dclay_instance_extradata.memory_pinned

    def set_memory_pinned(self, new_memory_pinned):
        """
        @postcondition: Set memory pinned flag of the object
        @param new_memory_pinned: memory pinned flag
        """
        self.__dclay_instance_extradata.memory_pinned = new_memory_pinned

    def get_dataset_id(self):
        """
        @postcondition: Return dataset id of the object 
        @return Data set id
        """
        return self.__dclay_instance_extradata.dataset_id
    
    def set_dataset_id(self, new_dataset_id):
        """
        @postcondition: Set dataset id of the object
        @param new_dataset_id: dataset id
        """
        self.__dclay_instance_extradata.dataset_id = new_dataset_id

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
                self.get_class_extradata().class_id
            )
        else:
            return None

    @classmethod
    def get_object_by_id(cls, object_id, *args, **kwargs):
        return getRuntime().get_object_by_id(object_id, *args, **kwargs)

    @classmethod
    def get_by_alias(cls, alias):
        return getRuntime().get_by_alias(alias)

    @classmethod
    def delete_alias(cls, alias):
        return getRuntime().delete_alias(alias)

    def set_persistent(self, ispersistent):
        """
        @postcondition: Set value of persistent flag in the object
        @param ispersistent: value to set
        """
        self.__dclay_instance_extradata.persistent_flag = ispersistent

    def set_loaded(self, isloaded):
        """
        @postcondition: Set value of loaded flag in the object
        @param isloaded: value to set
        """
        logger.verbose("Setting loaded to `%s` for object %s", isloaded, self.get_object_id())
        self.__dclay_instance_extradata.loaded_flag = isloaded

    def is_persistent(self):
        """
        @postcondition: Return TRUE if object is persistent. FALSE otherwise. 
        @return is persistent flag
        """
        return self.__dclay_instance_extradata.persistent_flag

    def is_loaded(self):
        """
        @postcondition: Return TRUE if object is loaded. FALSE otherwise. 
        @return is loaded flag
        """
        return self.__dclay_instance_extradata.loaded_flag
    
    def get_owner_session_id(self):
        """
        @postcondition: Get owner session id
        @return Owner session id
        """
        return self.__dclay_instance_extradata.owner_session_id
    
    def set_owner_session_id(self, the_owner_session_id):
        """
        @postcondition: Set ID of session of the owner of the object. 
        @param the_owner_session_id: owner session id 
        """ 
        self.__dclay_instance_extradata.owner_session_id = the_owner_session_id
    
    def is_pending_to_register(self):
        """
        @postcondition: Return TRUE if object is pending to register. FALSE otherwise. 
        @return is pending to register flag
        """
        return self.__dclay_instance_extradata.pending_to_register_flag
    
    def set_pending_to_register(self, pending_to_register):
        """
        @postcondition: Set pending to register flag. 
        @param pending_to_register: The flag to set
        """
        self.__dclay_instance_extradata.pending_to_register_flag = pending_to_register
    
    def is_dirty(self):
        """
        @postcondition: Return TRUE if object is dirty (it was modified). FALSE otherwise. 
        @return dirty flag
        """
        return self.__dclay_instance_extradata.dirty_flag
    
    def set_dirty(self, dirty_value):
        """
        @postcondition: Set dirty flag. 
        @param dirty_value: The flag to set
        """
        self.__dclay_instance_extradata.dirty_flag = dirty_value
    
    def get_hint(self):
        """
        @postcondition: Get hint
        @return Hint
        """
        return self.__dclay_instance_extradata.execenv_id
    
    def set_hint(self, new_hint):
        """
        @postcondition: Set hint
        @param new_hint: value to set
        """
        self.__dclay_instance_extradata.execenv_id = new_hint

    def federate(self, ext_dataclay_id, recursive=True):
        """
        @postcondition: Federates this object with an external dataClay instance
        @param ext_dataclay_id: id of the external dataClay instance
        @param recursive: Indicates if all sub-objects must be federated as well.
        """
        getRuntime().federate_object(self.get_object_id(), ext_dataclay_id, recursive,
                                     self.get_class_extradata().class_id, self.get_hint())
    
    def unfederate(self, ext_dataclay_id=None, recursive=True):
        """
        @postcondition: Unfederate this object with an external dataClay instance
        @param ext_dataclay_id: id of the external dataClay instance (none means to unfederate with all dcs)
        @param recursive: Indicates if all sub-objects must be unfederated as well.
        """
        if ext_dataclay_id is not None:
            getRuntime().unfederate_object(self.get_object_id(), ext_dataclay_id, recursive)
        else:
            getRuntime().unfederate_object_with_all_dcs(self.get_object_id(), recursive)          

    def get_external_dataclay_id(self, dcHost, dcPort):
        return getRuntime().ready_clients["@LM"].get_external_dataclay_id(dcHost, dcPort)

    def run_remote(self, backend_id, operation_name, value):
        return getRuntime().run_remote(self.get_object_id(), backend_id, operation_name, value)

    def get_external_dataclay_info(self, dataclay_id):
        """ Get external dataClay information
        :param dataclay_id: external dataClay ID
        :return: DataClayInstance information
        :type dataclay_id: UUID
        :rtype: DataClayInstance
        """
        return getRuntime().get_external_dataclay_info(dataclay_id)

    def get_federation_source(self):
        """ Retrieve dataClay instance id where the object comes from or NULL
        :return: dataClay instance ids where this object is federated
        :rtype: UUID
        """
        return getRuntime().get_external_source_of_dataclay_object(self.get_object_id())

    def get_federation_targets(self):
        """ Retrieve dataClay instances ids where the object is federated
        :return: dataClay instances ids where this object is federated
        :rtype: set of UUID
        """
        return getRuntime().get_dataclays_object_is_federated_with(self.get_object_id())

    def synchronize_federated(self, dc_info, operation_name, params):
        getRuntime().synchronize_federated(self, params, operation_name, dc_info)

    def serialize(self, io_file, ignore_user_types, iface_bitmaps,
                  cur_serialized_objs, pending_objs, reference_counting):
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
            if six.PY2:
                import cPickle as pickle
            elif six.PY3:
                import _pickle as pickle
            
            state = pickle.dumps(self.__getstate__(), protocol=-1)

            # Leave the previous value, probably False & True`
            dco_extradata.loaded_flag = last_loaded_flag
            dco_extradata.persistent_flag = last_persistent_flag

            StringWrapper(mode="binary").write(io_file, state)

        else:
            # Regular dataClay provided serialization
            # Get the list of properties, making sure it is sorted
            properties = sorted(
                self.get_class_extradata().properties.values(),
                key=attrgetter('position'))

            logger.verbose("Serializing list of properties: %s", properties)

            for p in properties:

                try:
                    value = object.__getattribute__(self, "%s%s" % (DCLAY_PROPERTY_PREFIX, p.name))
                except AttributeError:
                    value = None
                
                logger.verbose("Serializing property %s with value %s ", p.name, value)

                if value is None:
                    BooleanWrapper().write(io_file, False)
                else:
                    if isinstance(p.type, UserType):
                        if not ignore_user_types:
                            BooleanWrapper().write(io_file, True)
                            SerializationLibUtilsSingleton.serialize_association(io_file, value, cur_serialized_objs, pending_objs, reference_counting)
                        else: 
                            BooleanWrapper().write(io_file, False)
                    else:
                        BooleanWrapper().write(io_file, True)
                        pck = Pickler(io_file, protocol=-1)
                        pck.persistent_id = PersistentIdPicklerHelper(cur_serialized_objs, pending_objs, reference_counting)
                        pck.dump(value)

        # Reference counting
        # TODO: this should be removed in new serialization
        # TODO: (by using paddings to directly access reference counters inside metadata)
        
        cur_stream_pos = io_file.tell()
        io_file.seek(0)
        IntegerWrapper().write(io_file, cur_stream_pos)
        io_file.seek(cur_stream_pos)        
        reference_counting.serialize_reference_counting(self.get_object_id(), io_file)

    def deserialize(self, io_file, iface_bitmaps,
                    metadata,
                    cur_deserialized_python_objs):
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
            self.__dclay_instance_extradata.master_location = UUID(des_master_loc_str)

        if hasattr(self, "__setstate__"):
            # The object has a user-defined deserialization method.

            # Use pickle, and use that method instead            
            if six.PY2:
                import cPickle as pickle
            elif six.PY3:
                import _pickle as pickle
                
            state = pickle.loads(StringWrapper(mode="binary").read(io_file))
            self.__setstate__(state)

        else:
            # Regular dataClay provided deserialization

            # Start by getting the properties
            properties = sorted(
                self.get_class_extradata().properties.values(),
                key=attrgetter('position'))
            
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
                            value = DeserializationLibUtilsSingleton.deserialize_association(io_file, iface_bitmaps, metadata, cur_deserialized_python_objs, getRuntime())
                        except KeyError as e:
                            logger.error('Failed to deserialize association', exc_info=True)
                    else:
                        try:
                            upck = Unpickler(io_file)
                            upck.persistent_load = PersistentLoadPicklerHelper(
                                metadata, cur_deserialized_python_objs, getRuntime())
                            value = upck.load()
                        except:
                            traceback.print_exc()

                logger.debug("Setting value %s for property %s", value, p.name)

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
            logger.verbose("Pickling of object %r is causing a make_persistent", self)
            self.make_persistent()

        return _get_object_by_id_helper, (self.get_object_id(),
                                          self.get_class_extradata().class_id,
                                          self.get_hint())

    def __repr__(self):
        dco_extradata = self.__dclay_instance_extradata
        dcc_extradata = self.get_class_extradata()

        if dco_extradata.persistent_flag:
            return "<%s (ClassID=%s) instance with ObjectID=%s>" % \
                   (dcc_extradata.classname, dcc_extradata.class_id, dco_extradata.object_id)
        else:
            return "<%s (ClassID=%s) volatile instance with ObjectID=%s>" % \
                   (dcc_extradata.classname, dcc_extradata.class_id, dco_extradata.object_id)

    def __eq__(self, other):
        if not isinstance(other, DataClayObject):
            return False

        self_extradata = self.__dclay_instance_extradata
        other_extradata = other.__dclay_instance_extradata

        if not self_extradata.persistent_flag or not other_extradata.persistent_flag:
            return False

        return self_extradata.object_id and other_extradata.object_id \
            and self_extradata.object_id == other_extradata.object_id

    # FIXME: Think another solution, the user may want to override the method
    def __hash__(self):
        self_extradata = self.__dclay_instance_extradata
        return hash(self_extradata.object_id)

    @dclayMethod(obj='anything', property_name='str', value='anything', beforeUpdate='str', afterUpdate='str')
    def __setUpdate__(self, obj, property_name, value, beforeUpdate, afterUpdate):
        if beforeUpdate is not None:
            getattr(self, beforeUpdate)(property_name, value)
        object.__setattr__(obj, "%s%s" % ("_dataclay_property_", property_name), value)
        if afterUpdate is not None:
            getattr(self, afterUpdate)(property_name, value)
