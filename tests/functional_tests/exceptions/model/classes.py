
""" Class description goes here. """

from dataclay import dclayMethod

from storage.api import StorageObject


class Person(StorageObject):
    """
    @ClassField nicknames list<model.classes.Nickname>
    """

    @dclayMethod()
    def __init__(self):
        self.nicknames = list()

    @dclayMethod(return_=int)
    def __len__(self):
        return len(self.name)

    @dclayMethod(return_="anything")
    def __getitem__(self):
        return self.name, self.age

    @dclayMethod(return_="anything")
    def raise_exception(self):
        return self.nicknames[42]


class Nickname(StorageObject):
    """
    @ClassField nick str
    """

    @dclayMethod(nickname="str")
    def __init__(self, nickname):
        self.nick = nickname
