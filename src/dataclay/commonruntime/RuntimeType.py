
""" Class description goes here. """

from enum import Enum

__author__ = 'Alex Barcelo <alex.barcelo@bsc.es>'
__copyright__ = '2015 Barcelona Supercomputing Center (BSC-CNS)'


class RuntimeType(Enum):
    """Running modes of Python source in dataClay.

    Currently there exist the following modes:
      - [client] For client-side execution --outside dataClay.
      - [manage] The management mode for initialization/bootstraping the client.
      - [exe_env] Execution Environment mode (inside dataClay infrastructure).
    """
    client = 1
    manage = 2
    exe_env = 3
