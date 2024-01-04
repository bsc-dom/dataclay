from dataclay import DataClayObject, activemethod

class SensorValues(DataClayObject):
    values: list

    def __init__(self):
        self.values = list()

    @activemethod
    def add_element(self, new_value: float):
        self.values.append(new_value)

    @activemethod
    def public_data(self) -> float:
        return sum(self.values, 0.0) / len(self.values)
