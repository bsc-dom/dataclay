
""" Class description goes here. """

from dataclay import DataClayObject
from importlib import import_module
import logging

from dataclay.commonruntime.ExecutionGateway import loaded_classes
from dataclay.util.management.classmgr.UserType import UserType
from dataclay.exceptions.exceptions import DataClayException
import traceback
__author__ = 'Alex Barcelo <alex.barcelo@bsc.es'
__copyright__ = '2016 Barcelona Supercomputing Center (BSC-CNS)'

logger = logging.getLogger(__name__)


class MetaClassFactory(object):
    """Tracker of classes and generator of dataClay MetaClasses.

    One of the functions of this class is managing a set of classes, which
    may have cross dependencies between them. Additionally, this factory helps
    to manage a set of MetaClasses (prior to a registration process).

    The keyword parameters are used to complete the containers for the
    MetaClass being registered.
    """

    def __init__(self, namespace, responsible_account):
        """Simple class initialization.

        :param str namespace: The string of the namespace.
        :param str responsible_account: The registrator account (username).
        """
        self.classes = list()
        self.types = dict()

        self._responsible_account = responsible_account
        self._namespace = namespace

        self._prefix = None
        self._ignored_prefixes = -1

    def import_and_add(self, import_str):
        """Perform a import operation while adding classes.

        This method calls to importlib.import_module, while watching the
        StorageObject classes that are being loaded. All the classes that are
        loaded as a result of the import will be added to this factory.

        :param import_str: A string that can be used as parameter to import_module.
        """
        loaded_classes.clear()

        try:
            import_module(import_str)
        except ImportError as e:
            traceback.print_exc()
            logger.warning("Tried to import `%s` and failed, ignoring", import_str)
            logger.warning("Error: %s", e)
        else:
            for k in loaded_classes:
                if k.__module__.startswith("dataclay"):
                    # dataClay contrib classes should not be registered here
                    continue
                else:
                    self.add_class(k)

    def add_class(self, klass):
        """Add a class to this factory, from the class' Python object.

        Note that the caller provides de class, which should be an instance of
        ExecutionGateway.

        :param klass: The class object.
        """
        if not issubclass(klass, DataClayObject):
            raise DataClayException("Can only use DataClayObject classes")

        logger.verbose("Adding class %s to the MetaClassFactory", klass)
        class_container = klass._prepare_metaclass(
            self._namespace, self._responsible_account)

        # Save to the list, and bookmark the MetaClass
        # (for valid recursive behaviour, e.g. cycles)
        complete_name = class_container.name
        logger.debug("[add_class] Using `%s` as `name` field of Type",
                     complete_name)
        if complete_name not in self.types:
            self.types[complete_name] = UserType(
                signature="L{};".format(complete_name).replace(".", "/"),
                includes=[],
                namespace=self._namespace,
                typeName=complete_name)
        self.classes.append(class_container)

        parent = klass.__bases__[0]
        if parent is not DataClayObject:
            self.add_class(parent)

        logger.debug("Class %s finished", class_container.name)

    def __str__(self):
        return "MetaClass Factory containing:\n{}".format(str(self.classes))
