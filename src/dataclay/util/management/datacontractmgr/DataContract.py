
""" Class description goes here. """

from dataclay.util.MgrObject import ManagementObject


class DataContract(ManagementObject):
    _fields = ["dataClayID",
               "applicantsNames",
               "beginDate",
               "endDate",
               "publicAvailable",
               ]

    _internal_fields = ["providerAccountID",
                        "providerDataSetID",
                        "applicantsAccountsIDs",
                        ]
