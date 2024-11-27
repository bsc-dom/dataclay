"""
Public dataclay functions exported to use (friendly) "from dataclay import ..."
"""

from dataclay.client.api import Client
from dataclay.dataclay_object import DataClayObject, activemethod

from dataclay.alien import AlienDataClayObject  # isort: skip

StorageObject = DataClayObject

__version__ = "4.2.0-rc"
__all__ = ["Client", "DataClayObject", "AlienDataClayObject", "activemethod", "StorageObject"]
