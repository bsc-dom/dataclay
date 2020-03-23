from dataclay.util.IdentityDict import IdentityDict
import unittest as ut

class TestIdentityDict(ut.TestCase):

    def setUp(self):
        self.identity_dict = IdentityDict()
        self.key = 10
        self.value = 20

    def tearDown(self):
        pass
            
    def test_setitem(self):
        self.identity_dict.__setitem__(self.key, self.value)
        obtained_value = self.identity_dict[self.key]
        assert obtained_value == self.value

    def test_len(self):
        self.identity_dict.__setitem__(self.key, self.value)
        assert len(self.identity_dict) == 1
        
    def test_contains(self):
        self.identity_dict.__setitem__(self.key, self.value)
        assert self.key in self.identity_dict   

    def test_delitem(self):
        self.identity_dict.__setitem__(self.key, self.value)
        self.identity_dict.__delitem__(self.key)
        assert len(self.identity_dict) == 0
        
    def test_items(self):
        self.identity_dict.__setitem__(self.key, self.value)
        iterator = self.identity_dict.items()
        assert len(iterator) == 1
   
