
""" Class description goes here. """

from dataclay.util.MgrObject import ManagementObject


class StorageLocation(ManagementObject):
    _fields = ["dataClayID",
               "hostname",
               "name",
               "storageTCPPort",
               ]

    _internal_fields = []
