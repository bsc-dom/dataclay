import logging
from collections.abc import MutableMapping
from itertools import cycle
from typing import Any, Iterable

from dataclay import DataClayObject, activemethod

from . import splitting  # This is ourselves


class IdentityDict(MutableMapping):
    __slots__ = ("internal_dict",)

    def __init__(self):
        self.internal_dict = dict()

    def __setitem__(self, key, value):
        self.internal_dict[id(key)] = (key, value)

    def __getitem__(self, item):
        return self.internal_dict[id(item)][1]

    def items(self):
        return self.internal_dict.values()

    def __delitem__(self, key):
        del self.internal_dict[id(key)]

    def __len__(self):
        return len(self.internal_dict)

    # ToDo: this is not a valid canonical iteration of a dictionary (should be only the key)
    def __iter__(self):
        return self.internal_dict.values()

    def __contains__(self, item):
        return id(item) in self.internal_dict


logger = logging.getLogger(__name__)


#######################
# Note to the future: #
#######################
#
# The functions here may need some consistency and clean-up. The function
# `split` should become more well-defined, and the general behaviour of split,
# split_by_rows and the general idea of split_nd (the n-dimensional split)
# should be tied together somehow.
#
# There has been certain ontological discussions around this, and the points of
# view have clashed. This should also be related to the use cases; preliminar
# use cases have been built around a row-division of the data model, so the
# fancier splits were disregarded. Maybe some future use cases will prove this
# to be a wrong course of action. For now, you will see some dead code and
# unused/undocumented/untested functions in this file. Proceed with caution and
# have mercy on the pour souls that worked on this! (And also keep an open mind
# on the rationale and use cases that were considered at that point).
###############################################################################


def batch_object_info(objects):
    """Relying on object metadata (which may be outdated / wrong)."""

    logger.debug("Processing a batch_object_info call with #%d objects", len(objects))

    ret = IdentityDict()
    # Use hints
    for obj in objects:
        ret[obj] = obj._dc_master_backend_id

    return ret


class SplitCallResult:
    """Helper class for returning a coherent result on split calls."""

    def __init__(self, split_class, multiplicity=1):
        self.split_class = split_class
        self.multiplicity = multiplicity
        self.kv = dict()
        self.partitions = list()

        # split_class should derive from DataClayObject **and**
        # be a registered class (this last bit is not asserted).
        assert issubclass(split_class, DataClayObject)
        super().__init__()

    def add_by_ee(self, ee_key, obj_idx, obj):
        if ee_key not in self.kv:
            if self.multiplicity > 1:
                new_partitions = [self.split_class(ee_key) for _ in range(self.multiplicity)]

                self.kv[ee_key] = cycle(new_partitions)
                self.partitions.extend(new_partitions)
                partition = next(self.kv[ee_key])
            else:
                partition = self.split_class(ee_key)

                self.kv[ee_key] = partition
                self.partitions.append(partition)
        elif self.multiplicity > 1:
            partition = next(self.kv[ee_key])
        else:
            partition = self.kv[ee_key]

        partition.add_object(obj_idx, obj)


def _test_and_coerce_for_pobj(obj):
    """Test if the parameter is a PersistentObject, and coerce it into it.

    This function takes into account the corner cases of futures when the
    PyCOMPSs bindings are being used.

    This will return either (True, persistent_object) if obj is or represents
    a persistent object, and (False, wait_object) if obj is a persistent object
    nor a future representing it.
    """
    # The most common scenario, expedite it!
    if isinstance(obj, DataClayObject):
        return (True, obj)

    # Now let's start to look into the casuistics
    real_type = type(obj)

    if real_type.__name__ == "Future" and real_type.__module__.startswith("pycompss"):
        from pycompss.api.api import compss_wait_on

        waited_obj = compss_wait_on(obj)

        if isinstance(waited_obj, DataClayObject):
            return (True, waited_obj)
        else:
            return (False, waited_obj)
    else:
        return (False, obj)


def split(iterable, **split_options):
    """Perform a split on iterable.

    This method is highly inspired in the `iter` global method (in conjunction
    with its __iter__ counterpart method) for iterable classes.

    :param iterable: An iterable, which will typically be a Storage<Collection>
    :param split_options: The optional additional arguments to the split method.
    May be ignored.
    :return: A collection of Split, or something similar. If iterable is not a
    Storage<Collection>, returns a tuple with a single element, the iterable
    argument itself
    """
    try:
        # Default behaviour is to use the data model `split` method
        return iterable.split(**split_options)
    except AttributeError:
        return split_by_rows(iterable, **split_options)


def _split_helper(indexes, objects, split_class, **split_options):
    boi = batch_object_info(objects)

    multiplicity = split_options.get("multiplicity", 1)

    if split_class is None:
        result = SplitCallResult(GenericSplit, multiplicity=multiplicity)
    elif isinstance(split_class, str):
        result = SplitCallResult(getattr(splitting, split_class), multiplicity=multiplicity)
    else:
        result = SplitCallResult(split_class, multiplicity=multiplicity)

    # TODO: Check if everything below is useful and generic (e.g. for WorkStealingSplit)

    for idx, obj in zip(indexes, objects):
        ee = boi[obj]
        result.add_by_ee(ee, idx, obj)

    split_objects = result.partitions

    # TODO: This should be asynchronous / parallel
    for partition in split_objects:
        partition.make_persistent(backend_id=partition.backend)

    # Deprecating split_brothers as it incurs in a non-trivial performance penalty, allegedly

    return split_objects


def split_nd(gaggle, split_class=None, **split_options):
    """Perform a split on a n-dimensional structure containing persistent objects.

    Note that the input structure (`gaggle`) is expected to be a list or list-like
    with nested lists on itself --unless it is a 1-dimensional gaggle.
    """

    def gather_objects(subgaggle, curr_index=tuple()):
        """An ugly recursive approach."""
        indexes = list()
        objects = list()
        isdco, _ = _test_and_coerce_for_pobj(subgaggle[0])

        if not isdco:
            for i, hyperlist in enumerate(subgaggle):
                child_idx, child_obj = gather_objects(hyperlist, curr_index + (i,))
                indexes.extend(child_idx)
                objects.extend(child_obj)
        else:
            for i, item in enumerate(subgaggle):
                indexes.append(curr_index + (i,))

                # We may want to assert that *everything* is indeed a Persistent Object,
                # but doing so may incur in a substantial penalty.
                _, obj = _test_and_coerce_for_pobj(item)

                objects.append(obj)

        return indexes, objects

    indexes, objects = gather_objects(gaggle)

    return _split_helper(indexes, objects, split_class)


def split_1d(gaggle, split_class=None, **split_options):
    """Perform a split on a n-dimensional structure containing persistent objects.

    Note that the input structure (`gaggle`) is expected to be a list or list-like
    with nested lists on itself --unless it is a 1-dimensional gaggle.
    """
    indexes = range(len(gaggle))
    objects = [obj for _, obj in map(_test_and_coerce_for_pobj, gaggle)]

    return _split_helper(indexes, objects, split_class, **split_options)


# This function repeats a lot of code from the _split_helper, but there was no
# easy way of making it generic, and there may be more corner cases to handle
# or different strategies to implement.
def split_by_rows(gaggle, split_class=None, **split_options):
    """Perform a split on a 2-dimensional structure, splitting by rows.

    Note that the input structure (`gaggle`) is expected to be a list or list-like.
    """
    multiplicity = split_options.get("multiplicity", 1)

    # Gaggle may contain futures, let's coerce that
    rows = list()
    for row in gaggle:
        rows.append([obj for _, obj in map(_test_and_coerce_for_pobj, row)])

    # The strategy for now is: use the first element of each row for locality
    objects_to_consider = [row[0] for row in rows]

    boi = batch_object_info(objects_to_consider)

    if split_class is None:
        result = SplitCallResult(GenericSplit, multiplicity=multiplicity)
    elif isinstance(split_class, str):
        result = SplitCallResult(getattr(splitting, split_class), multiplicity=multiplicity)
    else:
        result = SplitCallResult(split_class, multiplicity=multiplicity)

    # TODO: Check if everything below is useful and generic (e.g. for WorkStealingSplit)

    for idx, row in enumerate(rows):
        ee = boi[row[0]]
        result.add_by_ee(ee, idx, row)

    split_objects = result.partitions

    # TODO: This should be asynchronous / parallel
    for partition in split_objects:
        partition.make_persistent(backend_id=partition.backend)

    # Deprecating split_brothers as it incurs in a non-trivial performance penalty, allegedly

    return split_objects


# Intended to be also collections.Iterable
class GenericSplit(DataClayObject):
    _chunks: list[DataClayObject]
    _idx: list
    split_brothers: list[DataClayObject]
    backend: Any

    def __init__(self, backend: Any):
        """Build a LocalIterator through a list of chunks.

        :param chunks: Sequence of (iterable) chunks.
        """
        # If this is not being called remotely, better to coerce to list right now
        self._chunks = list()
        self._idx = list()
        self.backend = backend
        self.split_brothers = list()

    @activemethod
    def add_object(self, idx, obj):
        self._chunks.append(obj)
        self._idx.append(idx)

    def __iter__(self):
        return iter(self._chunks)

    def get_indexes(self):
        return self._idx

    def enumerate(self):
        return zip(self._idx, self._chunks)


class WorkStealingSplit(GenericSplit):
    pass


class WorkMovingSplit(WorkStealingSplit):
    pass


class SplittableCollectionMixin(object):
    """Mixin to help the model programmer.

    This mixin is intended to be use with structures that have "chunks" (or
    some kind of internal partitioning) and desire to use them to provide high
    level "split iteration" abstractions.

    To provide support for SplittableCollections, include a get_chunks method
    which must return the list of chunks.
    """

    @activemethod
    def get_chunks(self) -> Iterable:
        try:
            return self.chunks
        except AttributeError:
            raise NotImplementedError(
                "ChunkedCollections must either implement the get_chunks method "
                "or contain a `chunks` attribute."
            )

    def split(self, split_class=None):
        from dataclay.contrib.splitting import split_1d

        return split_1d(self.get_chunks(), split_class=split_class)
