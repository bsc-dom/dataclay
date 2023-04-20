from dataclay import DataClayObject, activemethod


class Person(DataClayObject):

    name: str
    age: int

    @activemethod
    def __init__(self, name, age):
        self.name = name
        self.age = age


class Family(DataClayObject):

    members: list[Person]

    @activemethod
    def __init__(self, *args):
        self.members = list(args)

    @activemethod
    def add(self, new_member: Person):
        self.members.append(new_member)

    @activemethod
    def __str__(self) -> str:
        result = ["Members:"]

        for p in self.members:
            result.append(" - Name: %s, age: %d" % (p.name, p.age))

        return "\n".join(result)
