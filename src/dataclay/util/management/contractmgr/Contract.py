
""" Class description goes here. """

from dataclay.util.MgrObject import ManagementObject


class Contract(ManagementObject):
    _fields = ["dataClayID",
               "namespace",
               "beginDate",
               "endDate",
               "publicAvailable",
               "interfacesInContractSpecs",
               ]
    _internal_fields = ["providerAccountID",
                        "namespaceID",
                        "applicantsAccountsIDs",
                        "interfacesInContract",
                        ]
