
""" Class description goes here. """

from dataclay import StorageObject
from dataclay import dclayMethod
import logging

__author__ = 'Alex Barcelo <alex.barcelo@bsc.es>'
__copyright__ = '2016 Barcelona Supercomputing Center (BSC-CNS)'

CLASSES_TO_REGISTER = (
    "GenericSplit", "WorkStealingSplit", "WorkMovingSplit",
)
logger = logging.getLogger(__name__)


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
        # Otherwise, simply return a iterable which yields a single item
        return iterable,  # <- that comma is important!


# Intended to be also collections.Iterable
class GenericSplit(StorageObject):
    """Iterator to chain several chunks.

    @ClassField _chunks list<storageobject>
    @ClassField split_brothers list<storageobject>
    @ClassField storage_location anything
    @ClassField _current_chunk_idx int
    @ClassField _last_chunk_idx int
    """

    @dclayMethod(chunks="list<storageobject>", storage_location="anything")
    def __init__(self, chunks, storage_location):
        """Build a LocalIterator through a list of chunks.

        :param chunks: Sequence of (iterable) chunks.
        """
        # If this is not being called remotely, better to coerce to list right now
        self._chunks = list(chunks)
        self.storage_location = storage_location
        self.split_brothers = list()
        self._current_chunk_idx = -1
        self._last_chunk_idx = -1

        # non persistent field:
        self._current_iter_chunk = None

    @dclayMethod(return_=bool, _local=True)
    def _go_next_chunk(self):
        """Advance to next chunk.

        Prepare the internal chunk iterator. This is typically called when the
        current chunk iterator has finished. Return True if everything is ok,
        False if there is no valid next chunk.

        :return bool: Whether the advance is a success
        """
        self._current_chunk_idx += 1

        if self._current_chunk_idx < self._last_chunk_idx:
            self._current_iter_chunk = iter(self._chunks[self._current_chunk_idx])
            return True
        else:
            return False

    @dclayMethod(_local=True)
    def __next__(self):
        try:
            return next(self._current_iter_chunk)
        except StopIteration:
            logger.info("Iterator %s passing the chunk_idx %d", self.getID(), self._current_chunk_idx)

        if self._go_next_chunk():
            # At this point, for non-degenerate collections, means that there
            # is a chunk ready --so this is should not result in deep stack calls
            return next(self)
        else:
            raise StopIteration

    # Backwards compatibility to Python 2 (to be deprecated)
    @dclayMethod(_local=True)
    def next(self):
        return self.__next__()

    @dclayMethod()
    def _remote_iteration_init(self):
        """This method is used for remote initialization.

        This registered method is used by the local-execution `__iter__`. Given
        that that method is _local, a certain remote initialization must be
        ensured in order for the iteration to work smoothly.
        """
        self._current_chunk_idx = 0 if self._chunks else -1
        self._last_chunk_idx = len(self._chunks)

    # Note that the return is not serializable, thus the _local flag
    @dclayMethod(return_="anything", _local=True)
    def __iter__(self):
        # Prepare the remote stuff
        self._remote_iteration_init()

        # Prepare the iterators (non-serializable, `_local` specific)
        if self._chunks:
            self._current_iter_chunk = iter(self._chunks[0])
        else:
            self._current_iter_chunk = iter(list())

        # Now this object can be iterated
        return self


class WorkStealingSplit(GenericSplit):
    """Iterator to chain several chunks with simple Work Stealing addendum.

    The Work Stealing performed by this split is a simple one in which the
    chunk is returned to the thief, but no modifications are done (no movement,
    no reorganization of objects).

    @ClassField _chunks list<storageobject>
    @ClassField split_brothers list<storageobject>
    @ClassField storage_location anything
    @ClassField _current_chunk_idx int
    @ClassField _last_chunk_idx int
    """

    @dclayMethod(stolen_object="storageobject", return_="storageobject")
    def _post_stealing(self, stolen_object):
        """Not used by the simple base class WorkStealingSplit."""
        return stolen_object

    @dclayMethod(return_="storageobject")
    def steal_me(self):
        if self._current_chunk_idx < self._last_chunk_idx - 2:
            self._last_chunk_idx -= 1
            return self._chunks[self._last_chunk_idx]
        else:
            return None

    @dclayMethod(_local=True)
    def __next__(self):
        # TODO: the following lines (until "# Proceed to worksteal!") should be substituted by a super call
        try:
            return next(self._current_iter_chunk)
        except StopIteration:
            logger.info("Iterator %s passing the chunk_idx %d", self.getID(), self._current_chunk_idx)

        if self._go_next_chunk():
            return next(self)
        else:
            # Proceed to worksteal!
            import random
            # Use the list of brother locally [**]
            brothers = self.split_brothers
            while brothers:
                logger.info("Trying a brother...")
                victim_idx = random.randint(0, len(brothers) - 1)
                steal = brothers[victim_idx].steal_me()
                if steal is None:
                    logger.info("Split method could not steal from brother, removing")
                    brothers.pop(victim_idx)
                else:
                    logger.info("received %r", steal)
                    chunk_to_use = self._post_stealing(steal)
                    logger.info("using %r", chunk_to_use)
                    self._current_iter_chunk = iter(chunk_to_use)

                    # This will jump over the else
                    break
            else:
                # No valid targets to steal
                logger.info("No valid targets to steal")
                raise StopIteration

            # [**] re-store it for future usage (now that it may have been trimmed
            self.split_brothers = brothers
            return next(self)


class WorkMovingSplit(WorkStealingSplit):
    """Iterator to chain several chunks with Work Stealing through movement.

    The balancing performed by this split is similar to the simple Work Stealing
    but in this scenario the chunks are reorganized through movement. When there
    is a steal, the chunk is "physically" moved to the receiving end.

    @ClassField _chunks list<storageobject>
    @ClassField split_brothers list<storageobject>
    @ClassField storage_location anything
    @ClassField _current_chunk_idx int
    @ClassField _last_chunk_idx int
    """

    @dclayMethod(stolen_object="storageobject", return_="storageobject")
    def _post_stealing(self, stolen_object):
        """Once an object has been stolen, perform the movement."""
        # FIXME: We should not assume that this is server-side
        from dataclay.commonruntime.Runtime import getRuntime 
        from dataclay.commonruntime.Settings import settings
        getRuntime().move_object(stolen_object, settings.storage_id)
        return stolen_object


class SplittableCollectionMixin(object):
    """Mixin to help the model programmer.

    This mixin is intended to be use with Collections that have "chunks" (or
    some kind of internal partitioning) and desire to use them to provide high
    level "split iteration" abstractions.

    To provide support for SplittableCollections, include a get_chunks method
    which must return the list of chunks. Note that each chunk must have an
    iteration mechanism, with an structure that should resemble the original
    collection.
    """

    @dclayMethod(return_="anything")
    def get_chunks(self):
        try:
            return self.chunks
        except AttributeError:
            raise NotImplementedError("ChunkedCollections must either implement the get_chunks method "
                                      "or contain a `chunks` attribute.")

    # TODO: define the actual split method parameters (contact with Hecuba?).
    # TODO: Right now you can see "hardcoded" the "LocalIteration" behaviour
    @dclayMethod(return_="list<storageobject>", split_class="anything",
                 _local=True)
    def split(self, split_class=None):
        # TODO: this could be improved, library could cache stuff, or a joint call could be added
        from dataclay.commonruntime.Runtime import getRuntime
        location_chunks = sorted(
            (
                # Overly complex way to get a single ExecutionEnvironmentID
                # works in both Python2 & Python3
                next(iter(((getRuntime().get_all_locations(ch.get_object_id())).keys()))),
                ch
            ) for ch in self.get_chunks()
        )

        result = list()

        # FIXME: once support for imports has been implemented and tested, clean this up
        from itertools import groupby
        from operator import itemgetter
        from dataclay.contrib import splitting

        if split_class is None:
            split_class = splitting.GenericSplit
        elif isinstance(split_class, basestring):
            split_class = getattr(splitting, split_class)
        else:
            raise NotImplementedError("I could not understand %s (of type %s)" % 
                                      (split_class, type(split_class)))

        unused_exec_envs = set(getRuntime().get_execution_environments_info().keys())

        # FIXME: **********************************************************************************
        # FIXME: not using real split_class due to registration issues, but should be done that way
        # FIXME: **********************************************************************************

        for loc, chunks in groupby(location_chunks, key=itemgetter(0)):
            # Previous code using split intelligently:
            # split_object = split_class(map(itemgetter(1), chunks), loc)
            # split_object.make_persistent(backend_id=loc)
            # unused_exec_envs.remove(loc)
            # result.append(split_object)

            # Hacked around code:
            result.append(map(itemgetter(1), chunks))

        # Remove this
        return result

        # FIXME This is useful for WorkStealingSplit, but not for the others...
        for ee in unused_exec_envs:
            split_object = split_class(list(), ee)
            split_object.make_persistent(backend_id=ee)
            result.append(split_object)

        for split_object in result:
            # Note that this result is implicitly copied given that split is persistent
            # (maybe do the copy explicit? even when it is useless?)
            split_object.split_brothers = result

        return result
