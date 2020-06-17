
""" Class description goes here. """

from dataclay import dclayMethod

from storage.api import StorageObject


class Person(StorageObject):
    """
    @ClassField name anything
    @ClassField age int
    @ClassField nicknames list<model.classes.Nickname>
    """

    @dclayMethod(name="anything", age=int)
    def __init__(self, name, age):
        self.name = name
        self.age = age
        self.nicknames = list()

    @dclayMethod(return_=int)
    def __len__(self):
        return len(self.name)

    @dclayMethod(return_="anything")
    def __getitem__(self):
        return self.name, self.age

    @dclayMethod(nick="model.classes.Nickname")
    def add_nickname(self, nick):
        self.nicknames.append(nick)


class Nickname(StorageObject):
    """
    @ClassField nick str
    """

    @dclayMethod(nickname="str")
    def __init__(self, nickname):
        self.nick = nickname
