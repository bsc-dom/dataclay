"""Entry point for standalone dataClay Metadata server."""

from dataclay.conf import settings
from dataclay.metadata import servicer

settings.load_metadata_properties()
servicer.serve()
