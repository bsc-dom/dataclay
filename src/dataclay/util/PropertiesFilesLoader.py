
""" Class description goes here. """

"""Java `properties` parser.

A simple parser of the *.properties files can be found in this module. It is
not a complete and bulletproof implementation, but it is enough for simple
files.

See PropertyFile class for some considerations about the implementation.
"""

from abc import ABCMeta, abstractmethod
import re
import six

__author__ = 'Alex Barcelo <alex.barcelo@bsc.es>'
__copyright__ = '2015 Barcelona Supercomputing Center (BSC-CNS)'

""" Make this class abstract """


@six.add_metaclass(ABCMeta)
class PropertyFile(object):
    """Abstract property-holder class.

    All Property Files used in dataClay must have it own class, derived from
    this one. This function provides the basic line-by-line iteration and a
    commonruntime interface, but the details on each line stored data is dependant
    on each file.

    WARNING: ** Not implemented **
      - Multiline property lines
      - Escaping sequences
    """

    _prop_comment = re.compile(r"\s*([#!].*)?$")
    _prop_regular_line = re.compile(r"\s*(.*?)\s*[=:]\s*(.*)$")

    def __init__(self, file_name):
        """Open the file (which is expected to be a properties Java file) and read.

        This constructor relies on subclasses implementing their own
        process_line method, which will be called for each line.

        :param file_object: An object-like (stream) for the ".properties" file.
        :return:
        """
        with open(file_name, 'r') as file_object:
            for line in file_object:
                if not self._prop_comment.match(line):
                    m = self._prop_regular_line.match(line)
                    if m is not None:
                        self._process_line(m.group(1), m.group(2))

    @abstractmethod
    def _process_line(self, key, value):
        """Process a line of the ongoing properties file.

        This method should be implemented in derived classes and the internal
        class structure updated according to this properties' file needs.

        :param key: The key for the line being processed.
        :param value: The value (string) for the previous key.
        :return: None
        """
        return


class PropertyDict(PropertyFile):
    """Simple dictionary wrapper for a "properties" file."""

    def __init__(self, file_name):
        super(PropertyDict, self).__init__(file_name)

    def _process_line(self, key, value):
        """Simply store the values in the internal dictionary."""
        self.__dict__[key] = value
