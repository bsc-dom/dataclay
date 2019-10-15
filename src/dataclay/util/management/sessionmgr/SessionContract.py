
""" Class description goes here. """

from dataclay.util.MgrObject import ManagementObject


class SessionContract(ManagementObject):
    _fields = ["id",
               "contractID",
               "sessionInterfaces",
               ]

    _internal_fields = []
