
""" Class description goes here. """

from io import BytesIO
import six

from dataclay.serialization.python.DataClayPythonWrapper import DataClayPythonWrapper
from dataclay.serialization.python.lang.BooleanWrapper import BooleanWrapper
from dataclay.serialization.python.lang.IntegerWrapper import IntegerWrapper

__author__ = 'Alex Barcelo <alex.barcelo@bsc.es>'
__copyright__ = '2015 Barcelona Supercomputing Center (BSC-CNS)'


class StringWrapper(DataClayPythonWrapper):
    """String with different modes/encodings."""
    __slots__ = ("_mode", "_nullable")

    modes = {"utf-8", "utf-16", "binary"}

    def __init__(self, mode="utf-16", nullable=False):
        assert mode in self.modes, "The String mode should be one in {}".format(self.modes)
        self._mode = mode
        self._nullable = nullable

    def read(self, io_file):
        if self._nullable:
            is_not_null = BooleanWrapper().read(io_file)
            if not is_not_null:
                return None

        size = IntegerWrapper(32).read(io_file)
        ba = io_file.read(size)

        if self._mode == "utf-8":
            return ba.decode('utf-8')
        elif self._mode == "utf-16":
            return ba.decode('utf-16-be')
        elif self._mode == "binary":
            return ba
        else:
            raise TypeError("Internal mode {} not recognized".format(self._mode))

    def write(self, io_file, value):
        if self._nullable:
            if value is None:
                BooleanWrapper().write(io_file, False)
                return
            else:
                BooleanWrapper().write(io_file, True)

        if self._mode == "utf-8":
            ba = value.encode('utf-8')
        elif self._mode == "utf-16":
            ba = value.encode('utf-16-be')
        elif self._mode == "binary":
            if isinstance(value, BytesIO):
                ba = value.getvalue()
            else:
                if six.PY2:
                    ba = bytes(value)
                elif six.PY3:
                    ba = bytes(value, "utf-8")
        else:
            raise TypeError("Internal mode {} not recognized".format(self._mode))

        IntegerWrapper(32).write(io_file, len(ba))
        io_file.write(ba)
