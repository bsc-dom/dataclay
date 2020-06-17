
""" Class description goes here. """

from dataclay import dclayMethod
from storage.api import StorageObject

class Person(StorageObject):
    """
    @dclayReplication(afterUpdate='replicateToSlaves', inMaster='False')
    @ClassField name str
    @ClassField years int
    """

    @dclayMethod(name="str", years="int")
    def __init__(self, name, years):
        self.name = name
        self.years = years

    @dclayMethod(attribute="str", value="anything")
    def replicateToSlaves(self, attribute, value):
        from dataclay.DataClayObjProperties import DCLAY_SETTER_PREFIX
        for exeenv_id in self.get_all_locations().keys():
        #if not exeenv_id is master_location:
            self.run_remote(exeenv_id, DCLAY_SETTER_PREFIX + attribute, value)
            
    @dclayMethod(return_="anything")
    def getMyMasterLocation(self):
        return self.get_master_location()
