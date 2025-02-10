"""Easy to use distributable collections for dataClay.

This module provides a set of classes that can be used to store collections of
objects in a distributed manner. The collections are divided into chunks that
are stored in different dataClay backends. This allows for the collections to
grow without bound and still be efficiently accessed.
"""

from itertools import chain
from typing import Any, Optional
from uuid import UUID

from dataclay import DataClayObject, activemethod

from .splitting import SplittableCollectionMixin


class ListChunk(DataClayObject):
    """Chunk of a list.

    This class represents a chunk of a list. It is used to store a part of a
    list in a distributed manner. The chunk is stored in a single dataClay
    backend.
    """

    items: list

    def __init__(self, elements: list):
        self.items = elements[:]

    @activemethod
    def __getitem__(self, idx: int) -> Any:
        return self.items[idx]

    def __iter__(self) -> Any:
        # Note that the following cannot be serialized, hence the absence of @activemethod.
        return iter(self.items)

    @activemethod
    def __len__(self) -> int:
        return len(self.items)

    @activemethod
    def append(self, element: Any):
        self.items.append(element)


class DistributedList(DataClayObject, SplittableCollectionMixin):
    """Distributed list.

    This class represents a list that is distributed across multiple dataClay
    backends. The unit of distribution is a "chunk" (see `ListChunk`).
    """

    chunks: list[DataClayObject]
    chunk_size: int

    def __init__(self, initial_elements: Optional[list] = None, *, chunk_size=500):
        self.chunk_size = chunk_size
        if initial_elements:
            self.chunks = [ListChunk(initial_elements)]
        else:
            self.chunks = []

    @activemethod
    def append(self, element: Any):
        if self.chunks:
            last_chunk = self.chunks[-1]

            if len(last_chunk) < self.chunk_size:
                last_chunk.append(element)
                return

        # The collection was either empty or too crowded last element
        # So first prepare a new chunk
        new_chunk = ListChunk([element])

        # add the chunk to the list of chunks
        self.chunks.append(new_chunk)

    @activemethod
    def _add_chunk(self, chunk: DataClayObject):
        self.chunks.append(chunk)

    def extend(self, elements: list, backend_id: Optional[UUID] = None):
        chunk = ListChunk(elements)
        chunk.make_persistent(backend_id=backend_id)

        # Required because of the field remoteness
        self._add_chunk(chunk)

    @activemethod
    def __len__(self) -> int:
        return sum(map(len, self.chunks))

    def __iter__(self):
        # Note that the following cannot be serialized, hence the absence of @activemethod.
        return chain(*self.chunks)

    @activemethod
    def __getitem__(self, idx: int) -> Any:
        """Only integer indexes (no slices) are supported."""
        for chunk in self.chunks:
            l = len(chunk)
            if idx < l:
                return chunk[idx]
            else:
                idx -= l
        raise IndexError("index out of range")


class DictChunk(DataClayObject):
    """Chunk of a dictionary.

    This class represents a chunk of a dictionary. It is used to store a part of
    a dictionary in a distributed manner. The chunk is stored in a single dataClay
    backend.
    """

    elements: dict

    def __init__(self, elements):
        self.elements = {k: v for k, v in elements.items()}

    @activemethod
    def __getitem__(self, key: Any) -> Any:
        return self.elements[key]

    @activemethod
    def __setitem__(self, key: Any, value: Any):
        self.elements[key] = value

    @activemethod
    def __delitem__(self, key: Any):
        del self.elements[key]

    def __iter__(self):
        # Note that the following cannot be serialized, hence the absence of @activemethod.
        return iter(self.elements.keys())

    @activemethod
    def __contains__(self, item: Any) -> bool:
        return item in self.elements

    @activemethod
    def keys(self) -> list:
        return list(self.elements.keys())

    @activemethod
    def items(self) -> list:
        return list(self.elements.items())

    @activemethod
    def values(self) -> list:
        return list(self.elements.values())

    @activemethod
    def get(self, k: Any, default=None) -> Any:
        try:
            return self.elements[k]
        except KeyError:
            return default

    @activemethod
    def __len__(self) -> int:
        return len(self.elements)


class DistributedDict(DataClayObject, SplittableCollectionMixin):
    """Distributed dictionary.

    This class represents a dictionary that is distributed across multiple dataClay
    backends. The unit of distribution is a "chunk" (see `DictChunk`).

    This hash-based dictionary implementation ignores any rebalancing of
    the tree. That can be a problem for scalability. This architecture
    may change in future versions.
    """

    chunks: list[DataClayObject]
    num_buckets: int

    def __init__(self, initial_elements: Optional[dict] = None, *, num_buckets=16):
        # TODO: fix this magic number
        self.num_buckets = num_buckets
        self.chunks = [DictChunk({}) for i in range(self.num_buckets)]
        try:
            data = initial_elements.items()
        except AttributeError:
            data = iter(initial_elements)

        for k, v in data:
            self[k] = v

    def __iter__(self):
        # Note that the following cannot be serialized, hence the absence of @activemethod.
        return chain(iter(c) for c in self.chunks)

    def items(self):
        # Note that the following cannot be serialized, hence the absence of @activemethod.
        return chain(c.items() for c in self.chunks)

    def keys(self):
        # Note that the following cannot be serialized, hence the `_local` flag.
        return chain(c.keys() for c in self.chunks)

    def values(self):
        return chain(c.values() for c in self.chunks)

    @activemethod
    def __getitem__(self, key: Any) -> Any:
        h = hash(key) % self.num_buckets
        return self.chunks[h][key]

    @activemethod
    def __setitem__(self, key: Any, value: Any):
        h = hash(key) % self.num_buckets
        self.chunks[h][key] = value

    @activemethod
    def __delitem__(self, key: Any):
        h = hash(key) % self.num_buckets
        del self.chunks[h][key]

    @activemethod
    def __contains__(self, key: Any) -> bool:
        h = hash(key) % self.num_buckets
        return key in self.chunks[h]

    @activemethod
    def __len__(self) -> int:
        return sum(map(len, self.chunks))
