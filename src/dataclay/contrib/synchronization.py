"""Basic Synchronization mechanisms."""

from dataclay import dclayMethod


class ReplicateToAllMixin(object):
    """Simple replication mechanisms to all slaves.

    This mixin performs the replication by iterating all the locations of slave
    locations and performing the set operation in them.
    """
    @dclayMethod(attribute="str", value="anything")
    def replicate_mechanism(self, attribute, value):
        # This import should be there because this method will be in the stub
        from dataclay.DataClayObjProperties import DCLAY_SETTER_PREFIX
        for exeenv_id in self.get_all_locations().keys():
        #if not exeenv_id is master_location:
            self.run_remote(exeenv_id, DCLAY_SETTER_PREFIX + attribute, value)
