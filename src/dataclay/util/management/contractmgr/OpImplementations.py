
""" Class description goes here. """

from dataclay.util.MgrObject import ManagementObject


class OpImplementations(ManagementObject):
    _fields = ["id",
               "operationSignature",
               "numLocalImpl",
               "numRemoteImpl",
               ]

    _internal_fields = ["localImplementationID",
                        "remoteImplementationID",
                        ]
