
""" Class description goes here. """

from dataclay import dclayMethod
from storage.api import StorageObject

class Team(StorageObject):
    """
    @ClassField president tuple
    @ClassField coach tuple
    @ClassField players list
    """

class Player(StorageObject):
    """
    @ClassField personal_info tuple
    @ClassField carrer model.classes.Carrer
    @ClassField skills tuple
    @ClassField roles tuple
    @ClassField a bool
    @ClassField b int
    @ClassField c str
    @ClassField d set
    """
    
    @dclayMethod(name="str", surname="str", age=int)
    def __init__(self, name, surname, age):
        self.personal_info = (name, surname, age)
        self.roles = tuple()
        self.skills = tuple()

    @dclayMethod(carrer="model.classes.Carrer")
    def add_carrer(self, carrer):
        self.carrer = carrer

    @dclayMethod(role="str")
    def add_role(self, role):
        self.roles = (role,)

    @dclayMethod(skill="str")
    def add_skill(self, skill):
        self.skills = (skill,)
    
    @dclayMethod(a="bool", b="int", c="str",d="set")
    def add_test_types(self, a, b, c, d=None):
        self.a = a
        self.b = b
        self.c = c
        if d is not None:
            self.d = d 

class Carrer(StorageObject):
    """
    @ClassField stats dict
    @ClassField teams list
    """

    @dclayMethod()
    def __init__(self):
        self.stats = dict()
        self.teams = list()

    @dclayMethod(season="str",stat="dict")
    def add_stat(self, season, stat):
        self.stats[season] = stat

    @dclayMethod(season = "str", team = "str")
    def add_team(self, season, team):
        self.teams.append((season, team))

