from dataclay import DataClayObject, activemethod

class Employee(DataClayObject):
    name: str
    salary: float

    @activemethod
    def __init__(self, name, salary):
        self.name = name
        self.salary = salary

    @activemethod
    def get_payroll(self, hours_worked):
        overtime = 0
        if hours_worked > 40:
            overtime = hours_worked - 40
        return self.salary * (overtime * (self.salary / 40))
    
class Company(DataClayObject):
    name: str
    employees: list[Employee]

    @activemethod
    def __init__(self, name, *employees):
        self.name = name
        self.employees = list(employees)