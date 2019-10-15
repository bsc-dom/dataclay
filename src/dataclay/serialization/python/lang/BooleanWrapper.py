
""" Class description goes here. """

from dataclay.serialization.python.DataClayPythonWrapper import DataClayPythonWrapper
from dataclay.serialization.python.lang.IntegerWrapper import IntegerWrapper

__author__ = 'Alex Barcelo <alex.barcelo@bsc.es>'
__copyright__ = '2015 Barcelona Supercomputing Center (BSC-CNS)'


class BooleanWrapper(DataClayPythonWrapper):
    """One-byte bool type (0 means False)."""
    __slots__ = ()

    def __init__(self):
        pass

    def read(self, io_file):
        val = IntegerWrapper(8).read(io_file)
        if val == 0:
            return False
        else:
            return True

    def write(self, io_file, value):
        if value:
            IntegerWrapper(8).write(io_file, 0x01)
        else:
            IntegerWrapper(8).write(io_file, 0x00)

