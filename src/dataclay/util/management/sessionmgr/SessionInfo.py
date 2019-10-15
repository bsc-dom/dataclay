
""" Class description goes here. """

from dataclay.util.MgrObject import ManagementObject


class SessionInfo(ManagementObject):
    _fields = ["sessionID",
               "accountID",
               "propertiesOfClasses",
               "sessionContracts",
               "sessionDataContracts",
               "dataContractIDforStore",
               "language",
               "ifaceBitmaps",
               "endDate",
               ]

    _internal_fields = ["extDataClayID",
               ]
