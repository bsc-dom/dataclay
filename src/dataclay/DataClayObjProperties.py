""" Class description goes here. """

import logging
from collections import namedtuple

from dataclay.runtime import get_runtime

__author__ = "Alex Barcelo <alex.barcelo@bsc.es>"
__copyright__ = "2016 Barcelona Supercomputing Center (BSC-CNS)"

logger = logging.getLogger(__name__)

DCLAY_PROPERTY_PREFIX = "_dc_property_"
DCLAY_GETTER_PREFIX = "$$get"
DCLAY_SETTER_PREFIX = "$$set"
DCLAY_REPLICATED_SETTER_PREFIX = "$$rset"

PreprocessedProperty = namedtuple(
    "PreprocessedProperty",
    field_names=["name", "position", "type", "beforeUpdate", "afterUpdate", "inMaster"],
)


class DataclayProperty:

    __slots__ = "property_name", "dc_property_name"

    def __init__(self, property_name):
        self.property_name = property_name
        self.dc_property_name = DCLAY_PROPERTY_PREFIX + property_name

    def __get__(self, instance, owner):
        is_exec_env = get_runtime().is_exec_env()

        if (is_exec_env and instance._is_loaded) or (
            not is_exec_env and not instance._is_persistent
        ):
            try:
                instance._is_dirty = True
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
        if (is_exec_env and instance._is_loaded) or (
            not is_exec_env and not instance._is_persistent
        ):
            setattr(instance, self.dc_property_name, value)
            if is_exec_env:
                instance._is_dirty = True
        else:
            get_runtime().call_active_method(
                instance, "__setattr__", (self.property_name, value), {}
            )


# class ReplicatedDynamicProperty(DynamicProperty):
#     def __init__(self, property_name, before_method, after_method, in_master):
#         logger.debug(
#             "Initializing ReplicatedDynamicProperty %s | BEFORE = %s | AFTER = %s | INMASTER = %s",
#             property_name,
#             before_method,
#             after_method,
#             in_master,
#         )
#         super(ReplicatedDynamicProperty, self).__init__(property_name)
#         self.beforeUpdate = before_method
#         self.afterUpdate = after_method
#         self.inMaster = in_master

#     def __set__(self, obj, value):
#         """Setter for the dataClay property

#         See the __get__ method for the basic behavioural explanation.
#         """
#         logger.debug("Calling replicated setter for property %s", self.p_name)

#         is_client = not get_runtime().is_exec_env()
#         if is_client and not obj._is_persistent:
#             object.__setattr__(obj, "%s%s" % (DCLAY_PROPERTY_PREFIX, self.p_name), value)
#         elif not is_client and not obj._is_loaded:
#             get_runtime().call_active_method(obj, DCLAY_SETTER_PREFIX + self.p_name, (value,))
#         else:
#             if self.inMaster:

#                 get_runtime().call_active_method(
#                     obj,
#                     "__setUpdate__",
#                     (obj, self.p_name, value, self.beforeUpdate, self.afterUpdate),
#                 )
#             else:
#                 logger.debug(
#                     "Calling update locally for property %s with value %s", self.p_name, value
#                 )
#                 obj.__setUpdate__(obj, self.p_name, value, self.beforeUpdate, self.afterUpdate)
#             obj._is_dirty = True
