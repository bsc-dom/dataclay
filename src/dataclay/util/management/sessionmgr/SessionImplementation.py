
""" Class description goes here. """

from dataclay.util.MgrObject import ManagementObject


class SessionImplementation(ManagementObject):
    _fields = ["id",
               "implementationID",
               "namespaceID",
               "respAccountID",
               ]

    _internal_fields = []
