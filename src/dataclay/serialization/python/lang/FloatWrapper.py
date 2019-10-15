
""" Class description goes here. """

from struct import Struct
from dataclay.serialization.python.DataClayPythonWrapper import DataClayPythonWrapper

__author__ = 'Alex Barcelo <alex.barcelo@bsc.es>'
__copyright__ = '2015 Barcelona Supercomputing Center (BSC-CNS)'


class FloatWrapper(DataClayPythonWrapper):
    """Single or double precision floating value type."""
    __slots__ = ("_size", "_type")

    sizes = {32: Struct("!f"),
             64: Struct("!d")}

    def __init__(self, size=32):
        assert size in self.sizes, "Invalid size {:d} for integer type".format(size)
        self._size = size
        self._type = self.sizes[size]

    def read(self, io_file):
        val = io_file.read(self._size / 8)
        return self._type.unpack(val)[0]

    def write(self, io_file, value):
        io_file.write(self._type.pack(value))

