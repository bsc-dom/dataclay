
""" Class description goes here. """

from dataclay.util.MgrObject import ManagementObject
from dataclay.util.management.classmgr.Type import Type


class Operation(ManagementObject):
    _fields = ["dataClayID",
               "namespace",
               "className",
               "descriptor",
               "signature",
               "name",
               "nameAndDescriptor",
               "params",
               "paramsOrder",
               "returnType",
               "implementations",
               "isAbstract",
               "isStaticConstructor",
               ]

    _internal_fields = ["metaClassID",
                        "namespaceID",
                        "languageDepInfos",
                        "annotations"
                        ]

    _typed_fields = {"returnType": Type}
