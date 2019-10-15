
""" Class description goes here. """

"""Deactivate dataClay to allow sequential un-modified execution.

This will allow some loaded-modules-mangling and make dataClay classes
harmless.
"""

__author__ = 'Alex Barcelo <alex.barcelo@bsc.es>'
__copyright__ = '2017 Barcelona Supercomputing Center (BSC-CNS)'


class StorageObject(object):
    def make_persistent(self, *args, **kwargs):
        """This becomes a no-op."""
        pass


def dclayMethod(*args, **kwargs):
    return lambda f: f


def deactivate_storage_library():
    """Deactivate the mechanisms of the Storage Library.

    This should be called first thing, and will make sure that StorageObject
    and all that stuff is harmless and a no-op.
    """
    import dataclay
    import storage.api

    # Deactivate those things
    dataclay.DataClayObject = StorageObject
    dataclay.StorageObject = StorageObject
    dataclay.dclayMethod = dclayMethod

    # Also in the storage.api
    storage.api.StorageObject = StorageObject
