from dataclay import DataClayObject, activemethod


class StorageDict(DataClayObject):
    """Demonstration of the StorageDict class.

    This class is prepared for demonstration purposes and is not suitable,
    as it is right now, for HPC applications and production workflows.

    @ClassField _dict anything
    """
    _dict: dict

    @activemethod
    def __init__(self):
        self._dict = dict()

    @activemethod
    def __len__(self):
        return len(self._dict)

    @activemethod
    def __getitem__(self, key):
        return self._dict[key]

    @activemethod
    def __setitem__(self, key, value):
        self._dict[key] = value

    @activemethod
    def __delitem__(self, key):
        del self._dict[key]

    # Local because iterators are typically non-serializable
    @activemethod
    def __iter__(self):
        return iter(self._dict)

    @activemethod
    def __contains__(self, key):
        return key in self._dict

    # Local because dict.keys() returns a non-serializable object
    # (although it could be converted into a set or list)
    @activemethod
    def keys(self):
        return list(self._dict.keys())

    # Local because dict.items() returns a non-serializable object
    # (although it could be converted into a list)
    @activemethod
    def items(self):
        return list(self._dict.items())

    # Local because dict.values() returns a non-serializable object
    # (although it could be converted into a list)
    @activemethod
    def values(self):
        return list(self._dict.values())

    # Local because optional parameters for remote methods are not supported
    @activemethod
    def get(self, key, default=None):
        return self._dict.get(key, default)

    @activemethod
    def split(self):
        # Ugly split-in-two, for demonstration purposes only
        from itertools import cycle

        out_a = dict()
        out_b = dict()

        for (key, value), out in zip(self._dict.items(), cycle((out_a, out_b))):
            out[key] = value

        return (out_a, out_b)

    @activemethod
    def __str__(self):
        return "StorageDict(%s)" % str(self._dict)
