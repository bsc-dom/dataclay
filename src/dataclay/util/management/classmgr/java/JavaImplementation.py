
""" Class description goes here. """

from dataclay.util.management.classmgr.Implementation import Implementation


class JavaImplementation(Implementation):
    _fields = ["dataClayID"
               ]


""" _fields = ["position",
               "accessedProperties",
               "accessedImplementations",
               "includes",
               "prefetchingInfo",
               "reqQuantitativeFeatures",
               "reqQualitativeFeatures",
               "namespace",
               "className",
               "opNameAndDescriptor",     
              ]
"""

# ToDo: implement this (or leave a safe "ignore" mechanism for it)
# class JavaClassInfo(LanguageDependentContainer):
#     ...
""" _fileds = ["id",
               "signature",
               "javaParentInterfaces",
               "classByteCode",
              ]
"""
