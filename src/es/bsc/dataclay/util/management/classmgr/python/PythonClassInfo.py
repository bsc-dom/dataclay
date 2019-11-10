
""" Class description goes here. """

from es.bsc.dataclay.util.management.classmgr.LanguageDependantClassInfo import LanguageDependantClassInfo


class PythonClassInfo(LanguageDependantClassInfo):
    _fields = ["id",
               "imports",
               ]
