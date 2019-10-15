
""" Class description goes here. """

from struct import Struct
from dataclay.serialization.python.DataClayPythonWrapper import DataClayPythonWrapper

__author__ = 'Alex Barcelo <alex.barcelo@bsc.es>'
__copyright__ = '2015 Barcelona Supercomputing Center (BSC-CNS)'


class IntegerWrapper(DataClayPythonWrapper):
    """Multiple-size integer type."""
    __slots__ = ("_size", "_type")

    sizes = {8: Struct("!b"),
             16: Struct("!h"),
             32: Struct("!i"),
             64: Struct("!q")}

    def __init__(self, size=32):
        assert size in self.sizes, "Invalid size {:d} for integer type".format(size)
        self._size = size
        self._type = self.sizes[size]

    def read(self, io_file):
        val = io_file.read(int(self._size / 8))
        return self._type.unpack(val)[0]

    def write(self, io_file, value):
        io_file.write(self._type.pack(value))

