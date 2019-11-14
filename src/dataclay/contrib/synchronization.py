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
        # This import should be there because this method will be in the stub
        for exeenv_id in self.get_all_locations().keys():
        #if not exeenv_id is master_location:
            self.set_in_backend(exeenv_id, attribute, value)
            
    @dclayMethod(attribute="str", value="anything")
    def synchronize_federated(self, attribute, value):
        for dataclay_id in self.get_federation_targets():
            self.set_in_dataclay_instance(dataclay_id, attribute, [value])
        dataclay_id = self.get_federation_source()
        if dataclay_id is not None:
            self.set_in_dataclay_instance(dataclay_id, attribute, [value])
