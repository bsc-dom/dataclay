
""" Class description goes here. """

import uuid
from dataclay.serialization.python.DataClayPythonWrapper import DataClayPythonWrapper
from dataclay.serialization.python.lang.BooleanWrapper import BooleanWrapper

__author__ = 'Alex Barcelo <alex.barcelo@bsc.es>'
__copyright__ = '2015 Barcelona Supercomputing Center (BSC-CNS)'


class DCIDWrapper(DataClayPythonWrapper):
    """dataClay UUID (straightforward serialization)."""
    __slots__ = ("_nullable",)

    def __init__(self, nullable=False):
        self._nullable = nullable

    def read(self, io_file):
        if self._nullable:
            present = BooleanWrapper().read(io_file)
            if not present:
                return None
        return uuid.UUID(bytes=str(io_file.read(16)))

    def write(self, io_file, value):
        if self._nullable:
            if value is None:
                BooleanWrapper().write(io_file, False)
                return
            else:
                BooleanWrapper().write(io_file, True)

        io_file.write(value.get_bytes())
