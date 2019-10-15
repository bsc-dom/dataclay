
""" Class description goes here. """

from dataclay.util.MgrObject import ManagementObject

    
class DataClayInstance(ManagementObject):
    _fields = ["dcID",
               "hosts",
               "ports",
               ]

    _internal_fields = []
