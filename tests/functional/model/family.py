from __future__ import annotations
from dataclay import DataClayObject, activemethod


class Person(DataClayObject):

    name: str
    age: int
    spouse: Person
    dog: Dog

    @activemethod
    def __init__(self, name, age):
        self.name = name
        self.age = age
        self.spouse = None
        self.dog = None

    @activemethod
    def add_year(self):
        self.age += 1


class Dog(DataClayObject):

    name: str
    age: int
    puppies: list[Dog]

    @activemethod
    def __init__(self, name, age):
        self.name = name
        self.age = age
        self.dog_age = age * 7
        self.puppies = []

    @activemethod
    def add_year(self):
        self.age += 1
        self.dog_age = self.age * 7

    @activemethod
    def get_dog_age(self):
        try:
            return self.dog_age
        except Exception:
            self.dog_age = self.age * 7
            return self.dog_age

    @activemethod
    def new_puppy(self, name):
        puppy = Dog(name, 0)
        self.puppies.append(puppy)
        return puppy


class Family(DataClayObject):

    members: list[Person]

    @activemethod
    def __init__(self):
        self.members = list()

    @activemethod
    def add(self, new_member: Person):
        self.members.append(new_member)

    @activemethod
    def __str__(self) -> str:
        result = ["Members:"]

        for p in self.members:
            result.append(" - Name: %s, age: %d" % (p.name, p.age))

        return "\n".join(result)
