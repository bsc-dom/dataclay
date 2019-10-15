
""" Class description goes here. """

from dataclay.util.MgrObject import ManagementObject


class SessionOperation(ManagementObject):
    _fields = ["id",
               "operationID",
               "sessionLocalImplementation",
               "sessionRemoteImplementation",
               ]

    _internal_fields = []
