"""Entry point for standalone dataClay Backend server."""

from dataclay.backend import servicer
from dataclay.conf import settings

settings.load_backend_properties()
servicer.serve()
