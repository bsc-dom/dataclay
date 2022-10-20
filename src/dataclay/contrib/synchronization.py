"""Basic Synchronization mechanisms."""

from dataclay import dclayMethod


class SequentialConsistencyMixin(object):
    """Simple sequential consistency synchronization mechanism.

    This trivial sequential consistency consists on a immediate replication to
    all slaves. In order to achieve that, all the locations of slave locations
    are iterated and the set operation is performed in them.
    """

    @dclayMethod(attribute="str", value="anything")
    def synchronize(self, attribute, value):
        self.synchronize(attribute, value)
