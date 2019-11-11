
""" Class description goes here. """

from .Type import Type


# Deleted name from fields
class UserType(Type):
    _fields = [
               "namespace",
               ]

    _internal_fields = ["classID",
                        ]

