
""" Class description goes here. """

from dataclay.util.MgrObject import ManagementObject


class InterfaceInContract(ManagementObject):
    _fields = ["id",
               "iface",
               "implementationsSpecPerOperation",
               ]

    _internal_fields = ["interfaceID",
                        "accessibleImplementations",
                        ]
