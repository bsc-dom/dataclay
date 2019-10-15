
""" Class description goes here. """

from dataclay.util.MgrObject import ManagementObject


class Account(ManagementObject):
    _fields = ["username",
               "credential",
               "role",
               ]
