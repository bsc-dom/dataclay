
""" Class description goes here. """

from dataclay.util.MgrObject import ManagementObject


# Added implementationsByID and removed implementationsBySignature and implementationsByOpNameAndNumParams
class StubInfo(ManagementObject):
    _fields = ["namespace",
               "className",
               "parentClassName",
               "applicantID",
               "classID",
               "namespaceID",
               "contracts",
               "implementationsByID",
               "implementations",
               "properties",
               "propertyListWithNulls",
               ]

    _internal_fields = list()
