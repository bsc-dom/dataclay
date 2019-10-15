
""" Class description goes here. """

from dataclay.util.MgrObject import ManagementObject


class AccessedProperty(ManagementObject):
    _fields = [
               "id",  # sql id, internals
               "namespace",
               "className",
               "name",
               ]

    _internal_fields = ["propertyID",
                        ]

