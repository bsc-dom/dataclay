from __future__ import absolute_import
""" Class description goes here. """

""" 
Use absolute imports. By default, when you import a package in Python 2, it adds '.' in the beggining, it means all 
imports are relative. It's a problem for our testing since our test can be in a package but our stubs are not including 
the package of the test (and shouldn't!). With __future__ we add Python 3 functionality for all imports to be absolute. 
"""
# Initialize dataClay
import unittest 
import os
import sys
import traceback
from mock.mockdataclay import MockDataClay
import logging
import pytest

logger = logging.getLogger(__name__)


class WordCountTestCase(unittest.TestCase):

    """
    DataClayMock object for simulation. 
    """
    mock = None 
    """ 
    Number of nodes in this test
    """ 
    num_nodes = 1

    def setUp(self):
        """
        PyUnit function called before every test case.
        Starts DataClay simulation in one Python interpreter and one Java VM. This allows us to Debug in a local machine without 
        dockers and without a full start of DataClay (jars, configurations, ...) 
        """ 
        try:
            self.session_initialized = False
            self.mock = MockDataClay(self.num_nodes) 
            self.mock.startSimulation(__file__)            
            self.mock.newAccount("bsc", "password")
            self.mock.newDataContract("bsc", "password", "dstest", "bsc")
            self.mock.newNamespace("bsc", "password", "model", "python")
            
            class_path = os.path.dirname(os.path.abspath(__file__)) + "/model"
            stubs_path = os.path.dirname(os.path.abspath(__file__)) + "/stubs"
    
            contractid = self.mock.newModel("bsc", "password", "model", class_path)
            self.mock.getStubs("bsc", "password", contractid, stubs_path)
            
            dataclay_client_config = os.environ["DATACLAYCLIENTCONFIG"]
            self.mock.prepareSessionFiles("bsc", "password", stubs_path, "dstest", "dstest", dataclay_client_config, "DS1")
        except:
            traceback.print_exc()

    def tearDown(self):
        """ 
        Finish all services started for simulation. 
        """ 
        self.mock.finishSimulation()
    
    @unittest.skip("skipping wordcount compss test")
    def testWordCountWithCompss(self):
        """
        We execute test using COMPSs. COMPSs is going to run wordcount_compss_main.py directly. 
        """
        compss_main = os.path.dirname(os.path.abspath(__file__)) + "/compss/wordcount_compss_main.py"
        self.mock.runScriptUsingPyCOMPSs(compss_main)

        logger.debug("Test OK!")
