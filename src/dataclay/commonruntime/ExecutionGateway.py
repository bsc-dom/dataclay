"""Management of Python Classes.

This module is responsible of management of the Class Objects. A central Python
Metaclass is responsible of Class (not object) instantiation.

Note that this managers also includes most serialization/deserialization code
related to classes and function call parameters.
"""
from decorator import getfullargspec
import inspect
from logging import getLogger
import six

from dataclay.util.management.classmgr.MetaClass import MetaClass
from dataclay.util.management.classmgr.Operation import Operation
from dataclay.util.management.classmgr.Property import Property
from dataclay.util.management.classmgr.Type import Type
from dataclay.util.management.classmgr.Utils import STATIC_ATTRIBUTE_FOR_EXTERNAL_INIT
from dataclay.util.management.classmgr.python.PythonClassInfo import PythonClassInfo
from dataclay.util.management.classmgr.python.PythonImplementation import PythonImplementation
from dataclay.exceptions.exceptions import DataClayException

# Publicly show the dataClay method decorators
__author__ = 'Alex Barcelo <alex.barcelo@bsc.es>'
__copyright__ = '2016 Barcelona Supercomputing Center (BSC-CNS)'

logger = getLogger(__name__)

# Populated by ExecutionGateway, can be freely accessed and cleared (see MetaClassFactory)
loaded_classes = set()

# Class extradata caches
class_extradata_cache_exec_env = dict()
class_extradata_cache_client = dict()


class ExecutionGateway(type):
    """Python' Metaclass dataClay "magic"

    This type-derived Metaclass is used by DataClayObject to control the class
    instantiation and also object instances.
    """

    def __new__(mcs, classname, bases, dct):

        if classname == 'DataClayObject':
            # Trivial implementation, do nothing
            return super(ExecutionGateway, mcs).__new__(mcs, classname, bases, dct)
        # at this point, a real dataClay class is on-the-go
        klass = super(ExecutionGateway, mcs).__new__(mcs, classname, bases, dct)
        loaded_classes.add(klass)
        return klass

    def __init__(cls, name, bases, dct):
        logger.verbose("Initialization of class %s in module %s",
                       name, cls.__module__)

        super(ExecutionGateway, cls).__init__(name, bases, dct)

    def __call__(cls, *args, **kwargs):
        if cls.__name__ == 'DataClayObject':
            raise TypeError("Cannot create base objects")
        
        if getattr(cls, STATIC_ATTRIBUTE_FOR_EXTERNAL_INIT, False):
            logger.debug("New Persistent Instance (remote init) of class `%s`", cls.__name__)
            raise NotImplementedError("External initialization not implemented")
            # return getRuntime().new_persistent_instance_aux(cls, args, kwargs)
        else:
            ret = object.__new__(cls)  # this defers the __call__ method
            logger.debug("New regular dataClay instance of class `%s`", cls.__name__)

            # The following will trigger the initialize_object,
            # which will take care of volatile (in Execution Environment, ofc)
            ret._populate_internal_fields()

            # If there is a dclayMethod-decorated __init__, this will call that
            cls.__init__(ret, *args, **kwargs)

            return ret

    def new_dataclay_instance(cls, deserializing, **kwargs):
        """Return a new instance, without calling to the class methods."""
        logger.debug("New dataClay instance (without __call__) of class `%s`", cls.__name__)
        ret = object.__new__(cls)  # this defers the __call__ method
        ret._populate_internal_fields(deserializing=deserializing, **kwargs)
        return ret

    def _prepare_metaclass(cls, namespace, responsible_account):
        """Build a dataClay "MetaClass" for this class.

        :param str namespace: The namespace for this class' MetaClass.
        :param str responsible_account: Responsible account's username.
        :return: A MetaClass Container.
        """
        try:
            class_extradata = cls.get_class_extradata()
        except AttributeError:
            raise ValueError("MetaClass can only be prepared for correctly initialized DataClay Classes")

        logger.verbose("Preparing MetaClass container for class %s (%s)",
                       class_extradata.classname, class_extradata.full_name)

        # The thing we are being asked (this method will keep populating it)
        current_python_info = PythonClassInfo(
            imports=list()
        )
        current_class = MetaClass(
            namespace=namespace,
            name=class_extradata.full_name,
            parentType=None,
            operations=list(),
            properties=list(),
            isAbstract=False,
            languageDepInfos={'LANG_PYTHON': current_python_info}
        )

        ####################################################################
        # OPERATIONS
        ####################################################################
        predicate = inspect.isfunction if six.PY3 else inspect.ismethod
        for name, dataclay_func in inspect.getmembers(cls, predicate):
            # Consider only functions with _dclay_method
            if not getattr(dataclay_func, "_dclay_method", False):
                logger.verbose("Method `%s` doesn't have attribute `_dclay_method`",
                               dataclay_func)
                continue

            original_func = dataclay_func._dclay_entrypoint
            logger.debug("MetaClass container will contain method `%s`, preparing", name)

            # Skeleton for the operation
            current_operation = Operation(
                namespace=namespace,
                className=class_extradata.full_name,
                descriptor=str(),
                signature=str(),
                name=name,
                nameAndDescriptor=name,  # TODO: add descriptor?
                params=dict(),
                paramsOrder=list(),
                returnType=Type.build_from_type(dataclay_func._dclay_ret),
                implementations=list(),
                isAbstract=False,
                isStaticConstructor=False)

            # Start with parameters
            #########################

            # The actual order should be retrieved from the signature
            signature = getfullargspec(original_func)
            if signature.varargs or signature.varkw:
                raise NotImplementedError("No support for varargs or varkw yet")

            current_operation.paramsOrder[:] = signature.args[1:]  # hop over 'self'
            current_operation.params.update({k: Type.build_from_type(v)
                                             for k, v in dataclay_func._dclay_args.items()})

            if len(current_operation.paramsOrder) != len(current_operation.params):
                raise DataClayException("All the arguments are expected to be annotated, " \
                    "there is some error in %s::%s|%s" \
                                        % (namespace, class_extradata.full_name, name))

            # Follow by implementation
            ############################

            current_implementation = PythonImplementation(
                responsibleAccountName=responsible_account,
                namespace=namespace,
                className=class_extradata.full_name,
                opNameAndDescriptor=name,  # TODO: add descriptor?
                position=0,
                includes=list(),
                accessedProperties=list(),
                accessedImplementations=list(),
                requiredQuantitativeFeatures=dict(),
                requiredQualitativeFeatures=dict(),
                code=inspect.getsource(dataclay_func._dclay_entrypoint))

            current_operation.implementations.append(current_implementation)

            # Finally, add the built operation container into the class
            #############################################################
            current_class.operations.append(current_operation)

        ####################################################################
        # PROPERTIES
        ####################################################################
        for n, p in class_extradata.properties.items():
            current_property = Property(
                namespace=namespace,
                className=class_extradata.full_name,
                name=n,
                position=p.position,
                type=p.type,
                beforeUpdate=p.beforeUpdate,
                afterUpdate=p.afterUpdate,
                inMaster=p.inMaster)

            current_class.properties.append(current_property)

        ####################################################################
        # IMPORTS
        ####################################################################
        current_python_info.imports.extend(class_extradata.imports)

        return current_class
