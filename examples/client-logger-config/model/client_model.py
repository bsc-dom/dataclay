from dataclay import DataClayObject, activemethod


class Client_model(DataClayObject):

    name: str

    @activemethod
    def __init__(self, name):
        self.name = name

    @activemethod
    def change_name(self, name):
        self.name = name

    @activemethod
    def get_name(self):
        return self.name
