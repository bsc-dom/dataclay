"""
Public dataclay functions exported to use (friendly) "from dataclay import ..."
"""

from dataclay.client.api import Client
from dataclay.dataclay_object import DataClayObject, activemethod
from dataclay.alien import AlienDataClayObject
from dataclay.stub import StubDataClayObject

StorageObject = DataClayObject

__version__ = "4.2.0.dev"
__all__ = [
    "Client",
    "DataClayObject",
    "AlienDataClayObject",
    "StubDataClayObject",
    "activemethod",
    "StorageObject",
]
