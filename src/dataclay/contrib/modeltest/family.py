from __future__ import annotations

from dataclay import DataClayObject, activemethod
from dataclay.event_loop import run_dc_coroutine


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
    members: list[Person | Dog]

    @activemethod
    def __init__(self, *args):
        self.members = list(args)

    @activemethod
    def add(self, new_member: Person | Dog):
        self.members.append(new_member)

    @activemethod
    def __str__(self) -> str:
        result = ["Members:"]

        for p in self.members:
            result.append(" - Name: %s, age: %d" % (p.name, p.age))

        return "\n".join(result)

    # WARNING: Logic changed. Flush all now unloads all objects,
    # enven those that are running activemethods. This test is not valid anymore,
    # and will fail. Mutable attributes are not guaranteed to be consistent. To
    # guarantee consistency, use immutable attributes. The below code would work
    # if members was reassigned to the self.members attribute.
    @activemethod
    def test_self_is_not_unloaded(self):
        """Testing that while executing the activemethod in a Backend,
        the current instance must not be unloaded/nullified, in order to
        guarantee properties mutability.
        """
        from dataclay.config import get_runtime

        members = self.members

        run_dc_coroutine(get_runtime().data_manager.flush_all)

        dog = Dog("Rio", 4)
        members.append(dog)

        ##################
        # NOTE: Corrected line (check WARNING above)
        self.members = members
        ##################

        # If the current instance was nullified,
        # mutable "members" won't be consistent with the attribute
        assert members is self.members

    @activemethod
    def test_reference_is_unloaded(self):
        """
        DataClayObjects that are not self, can be unloaded in memory pressure.
        """
        from dataclay.config import get_runtime

        new_family = Family()
        members = new_family.members

        run_dc_coroutine(get_runtime().data_manager.flush_all)

        dog = Dog("Rio", 4)
        members.append(dog)
        assert members is not new_family.members
        assert members != new_family.members
