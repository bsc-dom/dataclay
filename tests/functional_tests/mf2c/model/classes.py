
""" Class description goes here. """

from dataclay import dclayMethod
from storage.api import StorageObject


class Component(StorageObject):
    """
    @ClassField sensor_type str
    @ClassField device_type str
    """

    @dclayMethod(sensor_type="str", device_type="str")
    def __init__(self, sensor_type, device_type):
        self.sensor_type = sensor_type
        self.device_type = device_type

    @dclayMethod(return_="str")
    def to_dict(self):
        return {
            "sensor_type": self.sensor_type,
            "device_type": self.device_type,
        }


class Device(StorageObject):
    """
    @ClassField device_id str
    @ClassField attached_components list<model.classes.Component>
    """
    @dclayMethod(device_id="str", attached_components="list<model.classes.Component>")
    def __init__(self, device_id, attached_components):
        self.device_id = device_id
        self.attached_components = attached_components


class Agent(StorageObject):
    """
    @ClassField id str
    @ClassField device model.classes.Device
    """

    @dclayMethod(my_device="model.classes.Device")
    def __init__(self, my_device):
        self.id = my_device.device_id
        self.device = my_device

    @dclayMethod(return_="list<model.classes.Component>")
    def get_attached_component_info(self):
        return self.device.attached_components

    @dclayMethod(return_="list")
    def get_attached_component_info_as_list(self):
        ret = list()
        for comp in self.get_attached_component_info():
            ret.append(comp.to_dict())
        return ret

    @dclayMethod(component="model.classes.Component")
    def add_attached_component(self, component):
        self.device.attached_components.append(component)
