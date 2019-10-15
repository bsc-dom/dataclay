
""" Class description goes here. """

from dataclay.util.management.classmgr.LanguageDependantClassInfo import LanguageDependantClassInfo


class PythonClassInfo(LanguageDependantClassInfo):
    _fields = ["id",
               "imports",
               ]
