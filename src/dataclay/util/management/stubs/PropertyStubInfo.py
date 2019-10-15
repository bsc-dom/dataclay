
""" Class description goes here. """

from dataclay.util.MgrObject import ManagementObject
from dataclay.util.management.classmgr.Type import Type


class PropertyStubInfo(ManagementObject):
    _fields = ["namespace",
               "propertyName",
               "namespaceID",
               "propertyID",
               "propertyType",
               "getterOperationID",
               "setterOperationID",
               "beforeUpdate",
               "afterUpdate",
               "inMaster"
               ]

    _internal_fields = list()

    _typed_fields = {"propertyType": Type}
