
""" Class description goes here. """

from storage.api import StorageObject
from dataclay import DataClayObject, dclayMethod
from dataclay.contrib.dummy_pycompss import *


class Mapa(DataClayObject):
    """
    @ClassField mapa dict<int, model.classes.Node>
    """

    @dclayMethod()
    def __init__(self):
        self.mapa = dict()

    @dclayMethod(new_node='model.classes.Node')
    def add(self, new_node):
        self.mapa[new_node.id] = new_node

    @dclayMethod(node='model.classes.Node')
    def delete(self, node):
        del self.mapa[node.id]

    # Immutable behaviour
    @dclayMethod(node='model.classes.Node')
    def modify(self, node):
        if node.id in self.mapa:
            self.mapa[node.id] = node

    @dclayMethod(node='model.classes.Node', return_='model.classes.Node')
    def get(self, node):
        return self.mapa[node.id]

    @dclayMethod(node='model.classes.Node', lon='float', lat='float')
    @task()
    def updateMap(self, node, lon, lat):
        node.updateJosm()
        node.lon = lon
        node.lat = lat
        node.updateJosm()


class Node(DataClayObject):
    """
    @ClassField id int
    @ClassField version int
    @ClassField changeset int
    @ClassField lon float
    @ClassField lat float
    
    """

    @dclayMethod(id='int', version='int', changeset='int', lon='float', lat='float')
    def __init__(self, iD, version, changeset, lon, lat):
        self.id = iD
        self.version = version
        self.changeset = changeset
        self.lon = lon
        self.lat = lat

    @dclayMethod(other='model.classes.Node', return_='bool')
    def __eq__(self, other):
        # Checking IDs it's enough -> ids are unique for each node
        return self.id == other.id
        # return self.id == other.id and self.lon == other.lon and self.lat == other.lat

    @dclayMethod(other='model.classes.Node', return_='bool')
    def __ne__(self, other):
        return not self.__eq__(other)
