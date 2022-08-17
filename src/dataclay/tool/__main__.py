from __future__ import print_function

""" Class description goes here. """

"""Entrypoint for tool execution.

This module can be executed with `python -m dataclay.tool <parameters>`.
"""
import sys

from . import functions

if len(sys.argv) < 2:
    # We need at least a parameter
    print("dataclay.tool requires at least the function parameter", file=sys.stderr)
    exit(1)

__name__ = sys.argv[1]
func = getattr(functions, __name__)

if not func:
    print(f"Unknown dataclay.tool function {func}", file=sys.stderr)
    exit(2)

func(*sys.argv[2:])
