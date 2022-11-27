from dataclay import DataClayObject, activemethod


class Person(DataClayObject):

    name: str
    age: int

    @activemethod
    def __init__(self, name, age):
        self.name = name
        self.age = age


class Company(DataClayObject):

    employees: list[Person]

    @activemethod
    def __init__(self):
        self.employees = list()

    @activemethod
    def add(self, new_employee: Person):
        self.employees.append(new_employee)

    @activemethod
    def __str__(self) -> str:
        result = ["Employees:"]

        for p in self.employees:
            result.append(" - Name: %s, age: %d" % (p.name, p.age))

        return "\n".join(result)
