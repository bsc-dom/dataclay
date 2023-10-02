from __future__ import annotations

from threading import Thread

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

    @activemethod
    def test_self_is_not_unloaded(self):
        """Testing that while executing the activemethod in a Backend,
        the current instance must not be unloaded/nullified, in order to
        guarantee properties mutability.
        """
        from dataclay.runtime import get_runtime

        members = self.members

        t = Thread(target=get_runtime().data_manager.flush_all, args=(0, False))
        t.start()
        t.join()

        dog = Dog("Rio", 4)
        members.append(dog)
        # If the current instance was nullified,
        # mutable "members" won't be consistent with the attribute
        assert members is self.members

    @activemethod
    def test_reference_is_unloaded(self):
        """
        DataClayObjects that are not self, can be unloaded in memory pressure.
        """
        from dataclay.runtime import get_runtime

        new_family = Family()
        members = new_family.members

        t = Thread(target=get_runtime().data_manager.flush_all, args=(0, False))
        t.start()
        t.join()

        dog = Dog("Rio", 4)
        members.append(dog)
        assert members is not new_family.members
        assert members != new_family.members


class TestActivemethod(DataClayObject):
    @activemethod
    def test_move_activemethod(self):
        from dataclay.runtime import get_runtime

        person = Person("Marc", 24)
        get_runtime().update_backend_clients()
        backend_ids = list(get_runtime().backend_clients)
        person.move(backend_ids[0])
        assert person._dc_meta.master_backend_id == backend_ids[0]
