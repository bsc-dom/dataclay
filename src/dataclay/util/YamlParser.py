"""Submodule for all the YAML-based management structures.

For specific information about the structures, see original Java implementation
--it is used as the authoritative implementation, available in util.management.

Note that the YAML dictionary-based fields are listed in the _fields attribute
and this is what is used on the load & dump YAML procedures.

For more information of the internal magic, see "MgrObject.py" file.

BLACK MAGIC WARNING! The NAME of the module (like "contractmgr") and the NAME
of the class (like "Contract") are used in order to obtain the YAML tag, which
will (hopefully) match the Java generated name, which comes from the Java
package name (like "!!util.management.contractmgr.Contract"). This is syntactic
sugar, but should be taken into account for cross-language correctness.
"""
from collections import namedtuple
from functools import partial
from yaml import Loader, load, dump

from dataclay.util.YamlIgnores import IGNORE_CLASSES, IGNORE_PREFIXES
from es.bsc.dataclay.util.ids import _uuid
from es.bsc.dataclay.util.info.VersionInfo import VersionInfo
from es.bsc.dataclay.util.management.accountmgr.Account import Account
from es.bsc.dataclay.util.management.classmgr.AccessedImplementation import AccessedImplementation
from es.bsc.dataclay.util.management.classmgr.AccessedProperty import AccessedProperty
from es.bsc.dataclay.util.management.classmgr.Implementation import Implementation
from es.bsc.dataclay.util.management.classmgr.MetaClass import MetaClass
from es.bsc.dataclay.util.management.classmgr.Operation import Operation
from es.bsc.dataclay.util.management.classmgr.Property import Property
from es.bsc.dataclay.util.management.classmgr.Type import Type
from es.bsc.dataclay.util.management.classmgr.UserType import UserType
from es.bsc.dataclay.util.management.classmgr.java.JavaImplementation import JavaImplementation
from es.bsc.dataclay.util.management.classmgr.python.PythonClassInfo import PythonClassInfo
from es.bsc.dataclay.util.management.classmgr.python.PythonImplementation import PythonImplementation
from es.bsc.dataclay.util.management.contractmgr.Contract import Contract
from es.bsc.dataclay.util.management.datacontractmgr.DataContract import DataContract
from es.bsc.dataclay.util.management.datasetmgr.DataSet import DataSet
from es.bsc.dataclay.util.management.interfacemgr.Interface import Interface
from es.bsc.dataclay.util.management.metadataservice.ExecutionEnvironment import ExecutionEnvironment
from es.bsc.dataclay.util.management.metadataservice.MetaDataInfo import MetaDataInfo
from es.bsc.dataclay.util.management.metadataservice.StorageLocation import StorageLocation
from es.bsc.dataclay.util.management.metadataservice.DataClayInstance import DataClayInstance
from es.bsc.dataclay.util.management.namespacemgr.Namespace import Namespace
from es.bsc.dataclay.util.management.sessionmgr.SessionContract import SessionContract
from es.bsc.dataclay.util.management.sessionmgr.SessionDataContract import SessionDataContract
from es.bsc.dataclay.util.management.sessionmgr.SessionImplementation import SessionImplementation
from es.bsc.dataclay.util.management.sessionmgr.SessionInfo import SessionInfo
from es.bsc.dataclay.util.management.sessionmgr.SessionInterface import SessionInterface
from es.bsc.dataclay.util.management.sessionmgr.SessionOperation import SessionOperation
from es.bsc.dataclay.util.management.sessionmgr.SessionProperty import SessionProperty
from es.bsc.dataclay.util.management.stubs.ImplementationStubInfo import ImplementationStubInfo
from es.bsc.dataclay.util.management.stubs.PropertyStubInfo import PropertyStubInfo
from es.bsc.dataclay.util.management.stubs.StubInfo import StubInfo
from dataclay.communication.grpc.messages.common.common_messages_pb2 import Langs

# Initialize (internal) representer/constructor for UUID
# and also all the ignores (literal maps)
__classes__ = [AccessedImplementation, AccessedProperty, Implementation, MetaClass,
    Operation, Property, Type, UserType, JavaImplementation,
    PythonImplementation, PythonClassInfo, Account, Contract,
    DataContract, DataSet, Namespace, Interface, ImplementationStubInfo,
    PropertyStubInfo, StubInfo, StorageLocation, DataClayInstance, SessionInfo, SessionContract,
    SessionOperation, SessionInterface, SessionImplementation, SessionDataContract,
    SessionProperty, MetaDataInfo, ExecutionEnvironment, VersionInfo]

__all__ = [clazz.__name__ for clazz in __classes__]


def trivial_constructor(loader, node):
    """Constructor used to "ignore" certain types.

    The behaviour is always to build a mapping. This is a harmless behaviour
    (at least, is expected to be). dataClay uses this for all want-to-ignore
    types, without losing semantics. If problems arise from this, this method
    could avoid them by returning None.

    For aesthetic reasons, a namedtuple instance is returned (which will be
    built tailored to the input, which may or may not be an expected behaviour)
    and its name will be used from the tag.
    """
    name = node.tag.rsplit(".", 1)[-1]
    contents = loader.construct_mapping(node)
    return namedtuple(name, contents.keys())(**contents)


def tuple_constructor(loader, node):
    ''' Constructor for a Java Tuple represented in YAML, which is is a simple two-element python tuple.
    :param loader: 
    :param node:
    :returns: None
    :rtype: None
    '''
    d = loader.construct_mapping(node)
    return d["first"], d["second"]


def feature_constructor(loader, node):
    """Feature (Java enum) is parsed as a String."""
    s = loader.construct_scalar(node)
    # Ugly hack, but we do not need the value at all
    return hash(s)


def lonely_equal_constructor(loader, node):
    """Solve/monkey-patch a very old bug.
    https://bitbucket.org/xi/pyyaml/issues/49/plain-equal-sign-as-node-content-results
    """
    s = loader.construct_scalar(node)
    return s


def lang_constructor(loader, node):
    """Language is parsed as a GRPC enum."""
    s = loader.construct_scalar(node)
    return Langs.Value(s)


Loader.add_constructor(u"tag:yaml.org,2002:value", lonely_equal_constructor)

# The tuple is a bit special itself
Loader.add_constructor(u"tag:yaml.org,2002:es.bsc.dataclay.util.structs.Tuple", tuple_constructor)

# Not needed for Python, but nice to avoid errors
Loader.add_constructor(u"tag:yaml.org,2002:es.bsc.dataclay.util.management.classmgr.features.Feature$FeatureType",
                       feature_constructor)

# The language is very special
Loader.add_constructor(u"tag:yaml.org,2002:es.bsc.dataclay.communication.grpc.messages.common.CommonMessages$Langs", lang_constructor)

for prefix in IGNORE_PREFIXES:
    yaml_tag_prefix = u"tag:yaml.org,2002:%s" % prefix
    Loader.add_multi_constructor(
        yaml_tag_prefix,
        # The following is used to disregard the tag
        lambda loader, _, node: trivial_constructor(loader, node))

for class_tag in IGNORE_CLASSES:
    yaml_class_tag = u"tag:yaml.org,2002:%s" % class_tag
    Loader.add_constructor(yaml_class_tag, trivial_constructor)
    
# Force all YAML usages to go through this class (so Loader is properly set)
dataclay_yaml_load = partial(load, Loader=Loader)
dataclay_yaml_dump = dump
