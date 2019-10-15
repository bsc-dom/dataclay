
""" Class description goes here. """

from dataclay.serialization.python.DataClayPythonWrapper import DataClayPythonWrapper

__author__ = 'Alex Barcelo <alex.barcelo@bsc.es>'
__copyright__ = '2015 Barcelona Supercomputing Center (BSC-CNS)'


class NullWrapper(DataClayPythonWrapper):
    """Null empty type."""
    __slots__ = ()

    def __init__(self):
        pass

    def read(self, io_file):
        return None

    def write(self, io_file, value):
        pass

