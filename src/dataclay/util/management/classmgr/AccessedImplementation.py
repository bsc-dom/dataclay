
""" Class description goes here. """

from dataclay.util.MgrObject import ManagementObject


class AccessedImplementation(ManagementObject):
    _fields = ["id",  # sql id, internals
               "namespace",
               "className",
               "opSignature",
               "implPosition",
               ]

    _internal_fields = ["implementationID",
                        ]

