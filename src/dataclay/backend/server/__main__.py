""" Class description goes here. """

"""Entry point for standalone dataClay Execution Environment server.

The main can be called easily through a

    python -m dclay_server
"""


from dataclay.util.config import CfgExecEnv
from dataclay import initialize
from dataclay.backend import servicer

initialize()


CfgExecEnv.set_defaults()
servicer.serve()
