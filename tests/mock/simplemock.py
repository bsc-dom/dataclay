
""" Class description goes here. """

'''
Created on Jan 9, 2018

@author: dgasull
'''
import os
import sys
import traceback
"""
Class for simple simulations
"""


class SimpleMock(object):
    
    """
    DataClayMock object for simulation. 
    """
    mock = None 
    """ 
    Number of nodes in this test
    """ 
    num_nodes = 0

    def setUp(self, test_file_path, nodes=1, ees_per_sl=1):

        from mock.mockdataclay import MockDataClay
        """
        PyUnit function called before every test case.
        Starts DataClay simulation in one Python interpreter and one Java VM. This allows us to Debug in a local machine without 
        dockers and without a full start of DataClay (jars, configurations, ...) 
        """ 
        self.num_nodes = nodes
        try:
            self.mock = MockDataClay(self.num_nodes, ees_per_sl=ees_per_sl) 
            self.mock.startSimulation(test_file_path)            
            self.mock.newAccount("bsc", "password")
            self.mock.newDataContract("bsc", "password", "dstest", "bsc")
            self.mock.newNamespace("bsc", "password", "model", "python")
            
            class_path = os.path.dirname(os.path.abspath(test_file_path)) + "/model"
            stubs_path = os.path.dirname(os.path.abspath(test_file_path)) + "/stubs"
    
            contractid = self.mock.newModel("bsc", "password", "model", class_path)
            self.mock.getStubs("bsc", "password", contractid, stubs_path)
            dataclay_client_config = os.path.dirname(os.path.abspath(__file__)) + "/client.properties"
            self.mock.prepareSessionFiles("bsc", "password", stubs_path, "dstest", "dstest", dataclay_client_config, "DS1")
        except Exception:
            traceback.print_exc()
            assert False

    def tearDown(self):
        """ 
        Finish all services started for simulation. 
        """ 
        self.mock.finishSimulation()
        
    def importStubModule(self, name):
        return self.mock.importStubModule(name)
