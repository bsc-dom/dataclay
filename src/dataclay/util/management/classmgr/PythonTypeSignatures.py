
""" Class description goes here. """

import os.path

from dataclay.util.PropertiesFilesLoader import PropertyFile

__author__ = 'Alex Barcelo <alex.barcelo@bsc.es>'
__copyright__ = '2015 Barcelona Supercomputing Center (BSC-CNS)'


class PythonTypeSignatures(PropertyFile):
    """Property holder for the "python_type_signatures.properties" file."""

    def __init__(self, property_path, python_type_name='python_type_signatures.properties'):
        super(PythonTypeSignatures, self).__init__(os.path.join(
            property_path, python_type_name))

    def _process_line(self, key, value):
        """The signatures are plain strings."""
        self.__dict__[key] = value
