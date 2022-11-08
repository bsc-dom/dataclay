""" Class description goes here. """

import logging
import traceback

from decorator import decorate

from dataclay.runtime import get_runtime

__author__ = "Alex Barcelo <alex.barcelo@bsc.es>"
__copyright__ = "2016 Barcelona Supercomputing Center (BSC-CNS)"

logger = logging.getLogger(__name__)

import functools


def activemethod(func):
    @functools.wraps(func)
    def wrapper_activemethod(self, *args, **kwargs):
        logger.verbose(f"Calling function {func.__name__}")
        try:
            # If the object is not persistent executes the method locally,
            # else, executes the method within the execution environment
            if (
                (get_runtime().is_exec_env() and self._is_loaded)
                or (get_runtime().is_client() and not self._is_persistent)
                or func.__name__ == "__setstate__"
                or func.__name__ == "__getstate__"
            ):
                return func(self, *args, **kwargs)
            else:
                return get_runtime().call_active_method(self, func.__name__, args)
        except Exception:
            traceback.print_exc()
            raise

    return wrapper_activemethod


def _dclayMethod(f, self, *args, **kwargs):
    """Helper function for DataClayObject method decoration"""
    logger.verbose(f"Calling function {f.__name__}")
    try:
        # If the object is not persistent executes the method locally,
        # else, executes the method within the execution environment
        if (
            (get_runtime().is_exec_env() and self._is_loaded)
            or (get_runtime().is_client() and not self._is_persistent)
            or f._dclay_local
            or f.__name__ == "__setstate__"
            or f.__name__ == "__getstate__"
        ):
            return f(self, *args, **kwargs)
        else:
            return get_runtime().call_active_method(self, f.__name__, args)
    except Exception:
        traceback.print_exc()
        raise


def _dclayEmptyMethod(f, self, *args, **kwargs):
    """Similar to dclayMethod, but without actual Python implementation."""
    logger.verbose(f"Calling (languageless) function {f.__name__}")

    # Let it fail elsewhere, if the user hacks around into an invalid state
    # (like a loaded&local non-persistent instance with an dclayEmptyMethod,
    #  something that should not happen normally)
    return get_runtime().call_active_method(self, f.__name__, args)


class dclayMethod:
    """Class-based decorator for DataClayObject method decoration"""

    def __init__(self, **kwargs):
        """Provide the argument type information

        The programmer is expected to set the same kwargs as the function,
        in addition to the `return_` special method return type.

        The typical usage is:

            @dclayMethod(a=int,
                         b='some.path.to.Class',  # this is valid (str)
                         c=imported.path.to.Class, # this is also valid
                         return_=None)
            def foo_bar(a, b, c):
                ...

        The method should be inside a DataClayObject derived class. See both
        DataClayObject class implementation and ExecutionGateway metaclass for
        more information about the internal behaviour.
        """
        self._method_args = kwargs

    def __call__(self, f):

        logger.verbose(f"Preparing dataClay method {f.__name__} with arguments {self._method_args}")
        decorated_func = decorate(f, _dclayMethod)
        decorated_func._dclay_entrypoint = f
        decorated_func._dclay_ret = self._method_args.pop("return_", None)
        decorated_func._dclay_args = self._method_args
        decorated_func._dclay_method = True

        # Store the local flag in both the function and the decorated function
        is_local = self._method_args.pop("_local", False)
        f._dclay_local = is_local
        # TODO: at the moment, this flag is ignored
        decorated_func._dclay_local = is_local

        # TODO: something more clever, or add the user-provided flag option at least
        decorated_func._dclay_readonly = False
        return decorated_func


def dclayEmptyMethod(f):
    """Simple (parameter-less) decorator for languageless methods."""
    decorated_func = decorate(f, _dclayEmptyMethod)
    decorated_func._dclay_method = True
    # TODO: something more clever, or add the user-provided flag option at least
    decorated_func._dclay_readonly = False
    return decorated_func
