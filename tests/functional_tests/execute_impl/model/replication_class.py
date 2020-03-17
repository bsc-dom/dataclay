
""" Class description goes here. """

from dataclay import dclayMethod
from storage.api import StorageObject

class Person(StorageObject):
    """
    @dclayReplication(beforeUpdate='beforeAttr', inMaster='True')
    @ClassField name str
    @ClassField years int
    """
    
    @dclayMethod(name="str", years="int")
    def __init__(self, name, years):
        self.name = name
        self.years = years

    @dclayMethod(attribute="str", value="anything")
    def beforeAttr(self, attribute, value):
        self.years = 3
