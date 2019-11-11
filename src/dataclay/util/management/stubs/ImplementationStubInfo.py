
""" Class description goes here. """

from dataclay.util.MgrObject import ManagementObject
from dataclay.util.management.classmgr.Type import Type


# Added implPosition
class ImplementationStubInfo(ManagementObject):
    _fields = ["namespace",
               "className",
               "signature",
               "params",
               "paramsOrder",
               "returnType",
               "namespaceID",
               "operationID",
               "localImplID",
               "remoteImplID",
               "contractID",
               "interfaceID",
               "responsibleRemoteAccountID",
               "implPosition",
               ]

    _internal_fields = list()

    _typed_fields = {"returnType": Type}

