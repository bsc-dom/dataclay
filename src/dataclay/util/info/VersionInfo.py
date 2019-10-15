
""" Class description goes here. """

from dataclay.util.MgrObject import ManagementObject


class VersionInfo(ManagementObject):
    _fields = ["versionOID",
               "versionsMapping",
               "locID",
               "originalMD",
               ]
