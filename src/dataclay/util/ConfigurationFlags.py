
""" Class description goes here. """

from dataclay.util.PropertiesFilesLoader import PropertyFile

__author__ = 'Alex Barcelo <alex.barcelo@bsc.es>'
__copyright__ = '2015 Barcelona Supercomputing Center (BSC-CNS)'


class ConfigurationFlags(PropertyFile):
    """Property holder for the "global.properties" file."""

    def __init__(self, property_path):
        super(ConfigurationFlags, self).__init__(property_path)

    def _process_line(self, key, value):
        """The signatures are plain strings."""
        self.__dict__[key] = value
