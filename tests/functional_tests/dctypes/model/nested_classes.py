
""" Class description goes here. """

from dataclay import dclayMethod
from storage.api import StorageObject

class NestedColl(StorageObject):
    """
    @ClassField a list
    @ClassField b dict
    @ClassField c tuple
    @ClassField d set
    """
    
    @dclayMethod(a="list", b="dict", c="tuple", d="set")
    def __init__(self, a, b, c, d):
        self.a = a
        self.b = b
        self.c = c
        self.d = d
    
    @dclayMethod(a="list", b="dict", c="tuple", d="set")
    def change_fields(self, a=None, b=None, c=None, d=None):
        if a is not None:
            self.a = a
        if b is not None:
            self.b = b
        if c is not None:
            self.c = c
        if d is not None:
            self.d = d
