
""" Class description goes here. """

from collections import namedtuple
import logging

from dataclay.commonruntime.Runtime import getRuntime

__author__ = 'Alex Barcelo <alex.barcelo@bsc.es>'
__copyright__ = '2016 Barcelona Supercomputing Center (BSC-CNS)'

logger = logging.getLogger(__name__)

DCLAY_PROPERTY_PREFIX = "_dataclay_property_"
DCLAY_GETTER_PREFIX = "$$get"
DCLAY_SETTER_PREFIX = "$$set"
DCLAY_REPLICATED_SETTER_PREFIX = "$$rset"

PreprocessedProperty = namedtuple('PreprocessedProperty', field_names=[
    'name', 'position', 'type', 'beforeUpdate', 'afterUpdate', 'inMaster'])


class DynamicProperty(property):
    """DataClay implementation of the `property` Python mechanism.

    This class is similar to property but is not expected to be used with
    decorators. Instead, the initialization is done from the ExecutionGateway
    metaclass, containing the required information about the property
    """
    __slots__ = ("p_name",)

    def __init__(self, property_name):
        logger.debug("Initializing DynamicProperty %s", property_name)
        """Initialize the DynamicProperty with the name of its property.

        Not calling super deliberately.

        The semantics and behaviour changes quite a bit from the property
        built-in, here we only store internally the name of the property and
        use dataClay friendly setters and getters.
        """
        self.p_name = property_name

    def __get__(self, obj, type_=None):
        """Getter for the dataClay property

        If the object is loaded, perform the getter to the local instance (this
        is the scenario for local instances and Execution Environment fully
        loaded instances).

        If the object is not loaded, perform a remote execution (this is the
        scenario for client remote instances and also Execution Environment
        non-loaded instances, which may either "not-yet-loaded" or remote)
        """
        is_exec_env = getRuntime().is_exec_env()
        logger.debug("Calling getter for property %s in %s", self.p_name,
                     "an execution environment" if is_exec_env else "the client")
        if (is_exec_env and obj.is_loaded()) or (not is_exec_env and not obj.is_persistent()):
            try:
                obj.set_dirty(True)  # set dirty = true for language types like lists, dicts, that are get and modified. TODO: improve this.
                return object.__getattribute__(obj, "%s%s" % (DCLAY_PROPERTY_PREFIX, self.p_name))
            except AttributeError:
                logger.warning("Received AttributeError while accessing property %s on object %r",
                               self.p_name, obj)
                logger.debug("Internal dictionary of the object: %s", obj.__dict__)
                raise
        else:
            return getRuntime().execute_implementation_aux(DCLAY_GETTER_PREFIX + self.p_name, obj, (), obj.get_hint())

    def __set__(self, obj, value):
        """Setter for the dataClay property

        See the __get__ method for the basic behavioural explanation.
        """
        logger.debug("Calling setter for property %s", self.p_name)

        is_exec_env = getRuntime().is_exec_env()
        if (is_exec_env and obj.is_loaded()) or (not is_exec_env and not obj.is_persistent()): 
            object.__setattr__(obj, "%s%s" % (DCLAY_PROPERTY_PREFIX, self.p_name), value)
            if is_exec_env: 
                obj.set_dirty(True)
        else:
            getRuntime().execute_implementation_aux(DCLAY_SETTER_PREFIX + self.p_name, obj, (value,), obj.get_hint())


class ReplicatedDynamicProperty(DynamicProperty):

    def __init__(self, property_name, before_method, after_method, in_master):
        logger.debug("Initializing ReplicatedDynamicProperty %s | BEFORE = %s | AFTER = %s | INMASTER = %s", property_name, before_method, after_method, in_master)
        super(ReplicatedDynamicProperty, self).__init__(property_name)
        self.beforeUpdate = before_method
        self.afterUpdate = after_method
        self.inMaster = in_master

    def __set__(self, obj, value):
        """Setter for the dataClay property

        See the __get__ method for the basic behavioural explanation.
        """
        logger.debug("Calling replicated setter for property %s", self.p_name)

        is_client = not getRuntime().is_exec_env()
        if is_client and not obj.is_persistent():
            object.__setattr__(obj, "%s%s" % (DCLAY_PROPERTY_PREFIX, self.p_name), value)
        elif not is_client and not obj.is_loaded():
            getRuntime().execute_implementation_aux(DCLAY_SETTER_PREFIX + self.p_name, obj, (value,), obj.get_hint())
        else:
            if self.inMaster:
                logger.debug("Calling update in master [%s] for property %s with value %s", obj.get_master_location, self.p_name, value)
                getRuntime().execute_implementation_aux('__setUpdate__', obj, (obj, self.p_name, value, self.beforeUpdate, self.afterUpdate), obj.get_master_location())
            else:
                logger.debug("Calling update locally for property %s with value %s", self.p_name, value)
                obj.__setUpdate__(obj, self.p_name, value, self.beforeUpdate, self.afterUpdate)
            obj.set_dirty(True)

