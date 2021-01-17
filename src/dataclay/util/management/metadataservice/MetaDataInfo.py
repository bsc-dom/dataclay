
""" Class description goes here. """

from dataclay.util.MgrObject import ManagementObject


class MetaDataInfo(ManagementObject):
    _fields = ["dataClayID",
               "isReadOnly",
               "datasetID",
               "metaclassID",
               "locations",
               "alias",
               "ownerID"
               ]

    _internal_fields = []
