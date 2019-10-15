
""" Class description goes here. """

from dataclay.util.MgrObject import ManagementObject

    
class SessionInterface(ManagementObject):
    _fields = ["id",
               "interfaceID",
               "sessionProperties",
               "sessionOperations",
               "classOfInterface",
               "importOfInterface",
               ]

    _internal_fields = []

