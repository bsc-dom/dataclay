from __future__ import absolute_import
""" Class description goes here. """

from dataclay import StorageObject
from dataclay import dclayMethod

from .splitting import SplittableCollectionMixin

__author__ = 'Alex Barcelo <alex.barcelo@bsc.es>'
__copyright__ = '2017 Barcelona Supercomputing Center (BSC-CNS)'

CLASSES_TO_REGISTER = (
    "StorageList", "ListChunk", "StorageDict", "DictChunk"
)


class ListChunk(StorageObject):
    """
    @ClassField items list<storageobject>
    """

    @dclayMethod(elements="list")
    def __init__(self, elements):
        self.items = elements[:]

    @dclayMethod(idx=int, return_="anything")
    def __getitem__(self, idx):
        return self.items[idx]

    @dclayMethod(return_="anything", _local=True)
    def __iter__(self):
        # Note that the following cannot be serialized, hence the `_local` flag.
        return iter(self.items)

    @dclayMethod(return_=int)
    def __len__(self):
        return len(self.items)

    @dclayMethod(element="anything")
    def append(self, element):
        self.items.append(element)


class StorageList(StorageObject, SplittableCollectionMixin):
    """
    @ClassField chunks list<storageobject>
    """

    @dclayMethod()
    def __init__(self):
        self.chunks = list()

    @dclayMethod(element="anything")
    def append(self, element):
        if self.chunks:
            last_chunk = self.chunks[-1]

            # FIXME: remove this MAGIC NUMBER
            if len(last_chunk) < 500:
                last_chunk.append(element)
                return

        # The collection was either empty or too crowded last element
        # So first prepare a new chunk
        new_chunk = ListChunk([element])

        # add the chunk to the list of chunks
        self.chunks.append(new_chunk)

    @dclayMethod(elements="list<storageobject>")
    def extend(self, elements):
        self.chunks.append(ListChunk(elements))

    @dclayMethod(elements="list<storageobject>", storage_location="anything", _local=True)
    def extend_on_location(self, elements, storage_location):
        chunk = ListChunk(elements)
        chunk.make_persistent(backend_id=storage_location)

        # Required because of the field remoteness
        chunks = self.chunks
        chunks.append(chunk)
        self.chunks = chunks

    @dclayMethod(return_=int)
    def __len__(self):
        return sum(len(chunk) for chunk in self.chunks)

    @dclayMethod(_local=True)
    def __iter__(self):
        from itertools import chain
        return chain(*self.chunks)

    @dclayMethod(return_="anything", idx=int)
    def __getitem__(self, idx):
        """Only integer indexes (no slices) are supported."""
        for chunk in self.chunks:
            l = len(chunk)
            if idx < l:
                return chunk[idx]
            else:
                idx -= l
        raise IndexError("index out of range")


class DictChunk(StorageObject):
    """
    @ClassField elements dict<anything, storageobject>
    """

    @dclayMethod(elements="dict")
    def __init__(self, elements):
        self.elements = {k: v for k, v in elements.items()}

    @dclayMethod(key="anything", return_="anything")
    def __getitem__(self, key):
        return self.elements[key]

    @dclayMethod(key="anything", value="storageobject")
    def __setitem__(self, key, value):
        self.elements[key] = value

    @dclayMethod(key="anything")
    def __delitem__(self, key):
        del self.elements[key]

    @dclayMethod(return_="anything", _local=True)
    def __iter__(self):
        # Note that the following cannot be serialized, hence the `_local` flag.
        return iter(self.elements.keys())

    @dclayMethod(item="anything", return_=bool)
    def __contains__(self, item):
        return item in self.elements

    @dclayMethod(return_="list<anything>")
    def keys(self):
        return list(self.elements.keys())

    @dclayMethod(return_="list<anything>")
    def items(self):
        return self.elements.items()

    @dclayMethod(return_="list<storageobject>")
    def values(self):
        return self.elements.values()

    @dclayMethod(k="anything", return_="storageobject")
    def get(self, k):
        try:
            return self.elements[k]
        except KeyError:
            return None

    @dclayMethod(return_=int)
    def __len__(self):
        return len(self.items)


class StorageDict(StorageObject, SplittableCollectionMixin):
    """
    ToDo: This hash-based dictionary implementation ignores any rebalancing of
    the tree. That doesn't seem right for scalability, but leaving that
    behaviour for the time being.

    @ClassField chunks list<storageobject>
    @ClassField num_buckets int
    """

    @dclayMethod(iterable="anything")
    def __init__(self, iterable):
        # TODO: fix this magic number
        self.num_buckets = 16
        self.chunks = [DictChunk({}) for i in range(self.num_buckets)]
        try:
            data = iterable.items()
        except AttributeError:
            data = iter(iterable)

        for k, v in data:
            self[k] = v

    @dclayMethod(return_="anything", _local=True)
    def __iter__(self):
        # Note that the following cannot be serialized, hence the `_local` flag.
        from itertools import chain
        return chain(iter(c) for c in self.chunks)

    # FIXME: CHECK AND TEST IT (Should change without iter)
    @dclayMethod(return_="anything", _local=True)
    def iteritems(self):
        # Note that the following cannot be serialized, hence the `_local` flag.
        from itertools import chain
        return chain(c.items() for c in self.chunks)

    @dclayMethod(return_="anything", _local=True)
    def iterkeys(self):
        # Note that the following cannot be serialized, hence the `_local` flag.
        from itertools import chain
        return chain(c.keys() for c in self.chunks)

    @dclayMethod(return_="anything", _local=True)
    def itervalues(self):
        # Note that the following cannot be serialized, hence the `_local` flag.
        from itertools import chain
        return chain(c.values() for c in self.chunks)

    @dclayMethod(key="anything", return_="storageobject")
    def __getitem__(self, key):
        h = hash(key) % self.num_buckets
        return self.chunks[h][key]

    @dclayMethod(key="anything", value="storageobject")
    def __setitem__(self, key, value):
        h = hash(key) % self.num_buckets
        self.chunks[h][key] = value

    @dclayMethod(key="anything")
    def __delitem__(self, key):
        h = hash(key) % self.num_buckets
        del self.chunks[h][key]

    @dclayMethod(key="anything", return_="bool")
    def __contains__(self, key):
        h = hash(key) % self.num_buckets
        return key in self.chunks[h]

    @dclayMethod(return_=int)
    def len(self):
        return sum(map(len, self.chunks))

    @dclayMethod(return_="list<anything>")
    def keys(self):
        from itertools import chain
        return list(chain(c.keys() for c in self.chunks))

    @dclayMethod(return_="list<anything>")
    def items(self):
        from itertools import chain
        return list(chain(c.items() for c in self.chunks))

    @dclayMethod(return_="list<storageobject>")
    def values(self):
        from itertools import chain
        return list(chain(c.values() for c in self.chunks))
