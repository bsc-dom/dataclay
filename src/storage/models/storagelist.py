from dataclay import DataClayObject, activemethod


class StorageList(DataClayObject):
    """Demonstration of the StorageList class.

    This class is prepared for demonstration purposes and is not suitable,
    as it is right now, for HPC applications and production workflows.

    @ClassField _list anything
    """

    @activemethod
    def __init__(self):
        self._list = list()

    @activemethod
    def __len__(self):
        return len(self._list)

    @activemethod
    def __contains__(self, item):
        return item in self._list

    @activemethod
    def append(self, item):
        self._list.append(item)

    # Local because iterators are typically non-serializable
    @activemethod
    def __iter__(self):
        return iter(self._list)

    @activemethod
    def split(self):
        # Ugly split-in-two, for demonstration purposes only
        from itertools import cycle

        out_a = list()
        out_b = list()

        for elem, out in zip(self._list, cycle(out_a, out_b)):
            out.append(elem)

        return (out_a, out_b)

    @activemethod
    def __getitem__(self, item):
        return self._list[item]

    @activemethod
    def __setitem__(self, item, value):
        self._list[item] = value

    @activemethod
    def __delitem__(self, item):
        del self._list[item]

    @activemethod
    def __str__(self):
        return "StorageList(%s)" % str(self._list)
