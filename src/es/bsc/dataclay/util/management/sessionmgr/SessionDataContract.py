
""" Class description goes here. """

from dataclay.util.MgrObject import ManagementObject


class SessionDataContract(ManagementObject):
    _fields = ["id",
               "dataContractID",
               "dataSetOfProvider",
               ]

    _internal_fields = []
