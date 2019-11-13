
""" Class description goes here. """

from ..LanguageDependantClassInfo import LanguageDependantClassInfo


class PythonClassInfo(LanguageDependantClassInfo):
    _fields = ["id",
               "imports",
               ]
