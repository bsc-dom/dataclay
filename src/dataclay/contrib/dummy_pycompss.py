""" Class description goes here. """

"""Module that implements dummy (no-op) stuff for PyCOMPSs.

What happens:
  - PyCOMPSs code should not be executed inside dataClay[1].
  - PyCOMPSs-ready classes should be valid classes inside dataClay.

The solution is implementing the decorators and basic constants as dummy no-op.

[1] This is assuming that nested tasks are not currently available from the
worker, and disregards the use case where a non-task dataClay method is called
from the master and its execution triggers a taskified dataClay method. It will
not be a task. Which seems a bug.
"""

__author__ = "Alex Barcelo <alex.barcelo@bsc.es>"
__copyright__ = "2017 Barcelona Supercomputing Center (BSC-CNS)"

# PyCOMPSs constants:
INOUT = None
IN = None
OUT = None
FILE_IN = None
FILE_OUT = None
FILE_INOUT = None
CONCURRENT = None


def task(*args, **kwargs):
    return lambda f: f


def constraint(*args, **kwargs):
    return lambda f: f
