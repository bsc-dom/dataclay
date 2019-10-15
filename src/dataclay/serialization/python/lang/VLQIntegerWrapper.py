
""" Class description goes here. """

from dataclay.serialization.python.DataClayPythonWrapper import DataClayPythonWrapper
from six import int2byte

__author__ = 'Alex Barcelo <alex.barcelo@bsc.es>'
__copyright__ = '2015 Barcelona Supercomputing Center (BSC-CNS)'

class VLQIntegerWrapper(DataClayPythonWrapper):
    """Variable Length Quantity."""
    __slots__ = ()

    def __init__(self):
        pass

    def read(self, io_file):
        value = 0
        while True:
            # Read one byte and build
            b = ord(io_file.read(1))
            value = (value << 7) + (b & 0x7F)

            # If the continuation bit (MSB) is zero, we are finished
            if (b & 0x80) == 0:
                return value

    # FIXME: Check with Python 2.7
    def write(self, io_file, value):
        if value == 0:
            io_file.write(b'\x00')
            return
        values = []
        while value > 0:
            # Put the 7-bit values into the list
            values.append(value & 0x7F)
            value >>= 7

        # Values with continuation bit activated
        for b in reversed(values[1:]):
            io_file.write(int2byte(0x80 | b))

        # Last value, no continuation bit
        io_file.write(int2byte(values[0]))
