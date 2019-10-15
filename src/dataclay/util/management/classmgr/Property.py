
""" Class description goes here. """

from dataclay.util.MgrObject import ManagementObject
from dataclay.util.management.classmgr.Type import Type

    
# Added setterImplementationID, deleted dataclayID
class Property(ManagementObject):
    _fields = ["dataClayID",
               "namespace",
               "className",
               "name",
               "position",
               "type",
               ]

    _internal_fields = ["getterOperationID",
                        "getterImplementationID",
                        "setterImplementationID",
                        "setterOperationID",
                        "updateOperationID",
                        "updateImplementationID",
                        "inMaster",
                        "beforeUpdate",
                        "afterUpdate",
                        "namespaceID",
                        "metaClassID",
                        "languageDepInfos",
                        "annotations"
                        ]

    _typed_fields = {"type": Type}
