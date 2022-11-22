""" Class description goes here. """

"""Entry point for standalone dataClay Execution Environment server.

The main can be called easily through a

    python -m dclay_server
"""


from dataclay.backend import servicer
from dataclay.conf import settings

# from dataclay import initialize

# initialize()

settings.load_backend_properties()
servicer.serve()
