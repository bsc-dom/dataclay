"""Deactivate dataClay to allow sequential un-modified execution.

This will allow some loaded-modules-mangling and make dataClay classes
harmless.
"""

__author__ = "Alex Barcelo <alex.barcelo@bsc.es>"
__copyright__ = "2017 Barcelona Supercomputing Center (BSC-CNS)"


class DataClayObject(object):
    def make_persistent(self, *args, **kwargs):
        """This becomes a no-op."""
        pass


def activemethod(f):
    return f


def deactivate_storage_library():
    """Deactivate the mechanisms of the Storage Library.

    This should be called first thing, and will make sure that StorageObject
    and all that stuff is harmless and a no-op.
    """
    import dataclay
    import storage.api

    # Deactivate those things
    dataclay.DataClayObject = DataClayObject
    dataclay.StorageObject = DataClayObject
    dataclay.activemethod = activemethod

    # Also in the storage.api
    storage.api.StorageObject = DataClayObject
