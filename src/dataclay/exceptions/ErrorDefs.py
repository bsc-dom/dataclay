
""" Class description goes here. """

import os.path

from dataclay.util.PropertiesFilesLoader import PropertyFile

__author__ = 'Alex Barcelo <alex.barcelo@bsc.es>'
__copyright__ = '2015 Barcelona Supercomputing Center (BSC-CNS)'


class ErrorCodes(PropertyFile):
    """Property holder for the "errorcodes.properties" file."""

    def __init__(self, property_path, error_codes_name="errorcodes.properties"):
        self.error_codes = {}
        super(ErrorCodes, self).__init__(os.path.join(property_path, error_codes_name))

    def _process_line(self, key, value):
        """The error codes are ints, and reverse lookup is useful."""
        error_code = int(value)
        self.__dict__[key] = error_code
        self.error_codes[error_code] = key
