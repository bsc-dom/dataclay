from dataclay import DataClayObject, dclayMethod


class StorageList(DataClayObject):
    """Demonstration of the StorageList class.

    This class is prepared for demonstration purposes and is not suitable,
    as it is right now, for HPC applications and production workflows.

    @ClassField _list anything
    """

    @dclayMethod()
    def __init__(self):
        self._list = list()

    @dclayMethod(return_="int")
    def __len__(self):
        return len(self._list)

    @dclayMethod(item="anything", return_="bool")
    def __contains__(self, item):
        return item in self._list

    @dclayMethod(item="anything")
    def append(self, item):
        self._list.append(item)

    # Local because iterators are typically non-serializable
    @dclayMethod(_local=True, return_="anything")
    def __iter__(self):
        return iter(self._list)

    @dclayMethod(return_="anything")
    def split(self):
        # Ugly split-in-two, for demonstration purposes only
        from itertools import cycle

        out_a = list()
        out_b = list()

        for elem, out in zip(self._list, cycle(out_a, out_b)):
            out.append(elem)

        return (out_a, out_b)

    @dclayMethod(item="anything", return_="anything")
    def __getitem__(self, item):
        return self._list[item]

    @dclayMethod(item="anything", value="anything")
    def __setitem__(self, item, value):
        self._list[item] = value

    @dclayMethod(item="anything")
    def __delitem__(self, item):
        del self._list[item]

    @dclayMethod(return_="str")
    def __str__(self):
        return "StorageList(%s)" % str(self._list)
