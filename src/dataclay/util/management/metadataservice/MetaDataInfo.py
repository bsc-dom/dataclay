
""" Class description goes here. """

from dataclay.util.MgrObject import ManagementObject


class MetaDataInfo(ManagementObject):
    _fields = ["dataClayID",
               "isReadOnly",
               "datasetID",
               "metaclassID",
               "locations",
               "aliases",
               "ownerID"
               ]

    _internal_fields = []
