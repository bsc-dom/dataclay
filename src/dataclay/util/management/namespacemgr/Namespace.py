
""" Class description goes here. """

from dataclay.util.MgrObject import ManagementObject


class Namespace(ManagementObject):
    _fields = ["dataClayID",
               "providerAccountName",
               "name",
               ]

    _internal_fields = ["responsible",
                        "importedInterfaces",
                        "language",
                        ]
