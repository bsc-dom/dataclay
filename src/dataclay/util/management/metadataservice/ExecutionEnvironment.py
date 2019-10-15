
""" Class description goes here. """

from dataclay.util.MgrObject import ManagementObject

    
class ExecutionEnvironment(ManagementObject):
    _fields = ["dataClayID",
               "hostname",
               "name",
               "port",
               "lang"
               ]

    _internal_fields = []
