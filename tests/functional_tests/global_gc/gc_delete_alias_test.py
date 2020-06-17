from __future__ import absolute_import
""" Class description goes here. """

""" 
Use absolute imports. By default, when you import a package in Python 2, it adds '.' in the beggining, it means all 
imports are relative. It's a problem for our testing since our test can be in a package but our stubs are not including 
the package of the test (and shouldn't!). With __future__ we add Python 3 functionality for all imports to be absolute. 
"""
# Initialize dataClay
from mock.simplemock import SimpleMock
import unittest 
import os
import resource
import time
import gc
import sys
from unittest.case import SkipTest
import logging
import pytest
import traceback
from dataclay.util import Configuration

"""
Memory testing. 
"""
logger = logging.getLogger(__name__)


class GCUpdateTestCase(unittest.TestCase):

    """
    DataClayMock object for simulation. 
    """
    
    mock = SimpleMock() 
    
    def setUp(self):
        """
        PyUnit function called before every test case.
        Starts DataClay simulation in one Python interpreter and one Java VM. This allows us to Debug in a local machine without 
        dockers and without a full start of DataClay (jars, configurations, ...) 
        """ 
        Configuration.MEMMGMT_PRESSURE_FRACTION = 0.01
        self.mock.setUp(__file__)

    def tearDown(self):
        """ 
        Finish all services started for simulation. 
        """ 
        self.mock.tearDown()
    
    @pytest.mark.timeout(1000, method='thread')
    def test(self):
        """Test. note that all test method names must begin with 'test.'"""
        """WARNING: IT IS HIGHLY RECOMMENDED TO HAVE ONE TEST ONLY TO ISOLATE FUNCTIONAL TESTS FROM EACH OTHER. i.e. 
        Start a new Python Interpreter and JVM for each test. In the end, it means only one test in this class. """
        from dataclay.api import init, finish

        logger.debug('**Starting init**')
        init()
        
        """ 
        Imports. Imports must be located here in order to simulate "import" order in a real scenario. 
        VERY IMPORTANT: Imports must be located AFTER init
        """
        from model.classes import WebSite, WebPage, URI
        self.session_initialized = True
    
        """
        Test. From now on, the Functional Test itself. 
        """
        uri = URI("host/bsc")
        try:
            uri.make_persistent(alias="thealias")
        except:
            traceback.print_exc()
        
        from dataclay import getRuntime
        getRuntime().close_session()
        
        # Check if object exists
        time.sleep(20)
        self.assertTrue(self.mock.mock.mock_dataclay.objectExists(str(uri.get_object_id())))
            
        # Remove the alias 
        URI.delete_alias("thealias")
        
        # Check if object exists
        while self.mock.mock.mock_dataclay.objectExists(str(uri.get_object_id())):
            print("Waiting... ")
            time.sleep(5)
            
        logger.debug("Test OK!")
	    
