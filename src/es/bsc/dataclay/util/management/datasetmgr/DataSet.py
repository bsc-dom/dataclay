
""" Class description goes here. """

from dataclay.util.MgrObject import ManagementObject


class DataSet(ManagementObject):
    _fields = ["dataClayID",
               "name"
               ]

    _internal_fields = ["providerAccountID",
                        ]
