from dataclay import DataClayObject, activemethod

# from dataclay.contrib.mqtt import MQTTMixin


class Dog(DataClayObject):
    name: str
    race: str
    age: str

    @activemethod
    def __init__(self, name, age):
        self.name = name
        self.age = age

    @activemethod
    def set_race(self, race):
        self.race = race

    @activemethod
    def new_dog(self, name):
        dog = Dog(name, 99)
        return dog


class Criminal(DataClayObject):
    name: str
    detained: bool

    @activemethod
    def __init__(self, name):
        self.name = name
        self.detained = False


class Police(DataClayObject):

    name: str
    dog: Dog

    @activemethod
    def __init__(self, name):
        self.name = name

    @activemethod
    def set_dog(self, dog):
        self.dog = dog

    @activemethod
    def detain(self, criminal: Criminal, detentions: list):
        criminal.detained = True
        detentions.append(criminal.name)


class Person(DataClayObject):

    name: str
    age: int

    @activemethod
    def __init__(self, name, age):
        self.name = name
        self.age = age


class People(DataClayObject):

    people: list[Person]

    @activemethod
    def __init__(self):
        self.people = list()

    @activemethod
    def add(self, new_person: Person):
        self.people.append(new_person)

    @activemethod
    def __str__(self) -> str:
        result = ["People:"]

        for p in self.people:
            result.append(" - Name: %s, age: %d" % (p.name, p.age))

        return "\n".join(result)


class TestPerson(DataClayObject):
    @activemethod
    def test_dataset(self, alias: str, dataset: str):
        new_person = Person(name="Marc-" + str(dataset), age=32)
        # new_person.make_persistent()
        # new_person.make_persistent(dataset_name=dataset)
        new_person.make_persistent()

        # ref_person = Person.get_by_alias(alias, dataset)
        # assert new_person.name == ref_person.name
        print("test_dataset OK")

    @activemethod
    def test_get_by_alias(self, alias: str):
        new_person = Person(name="Alice", age=32)
        new_person.make_persistent(alias)
        ref_person = Person.get_by_alias(alias)
        assert new_person.name == ref_person.name
        print("test_get_by_alias OK")

    @activemethod
    def test_delete_alias(self, alias: str):
        new_person = Person(name="Alice", age=32)
        new_person.make_persistent(alias)
        Person.delete_alias(alias)
        print("test_delete_alias OK")


# class SomeClass(DataClayObject, MQTTMixin):

#     name: str
#     age: int

#     @activemethod
#     def __init__(self, name: str, age: int):
#         self.name = name
#         self.age = age
