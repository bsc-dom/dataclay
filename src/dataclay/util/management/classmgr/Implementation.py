
""" Class description goes here. """

from dataclay.util.MgrObject import ManagementObject


class Implementation(ManagementObject):
    _fields = ["dataClayID",
               "responsibleAccountName",
               "namespace",
               "className",
               "opNameAndDescriptor",
               "position",
               "includes",
               "accessedProperties",
               "accessedImplementations",
               "requiredQuantitativeFeatures",
               "requiredQualitativeFeatures",
               ]

    _internal_fields = ["operationID",
                        "metaClassID",
                        "responsibleAccountID",
                        "namespaceID",
                        "prefetchingInfo",
                        ]
