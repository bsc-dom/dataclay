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
import logging
import pytest

"""
Replication testing. 
"""
logger = logging.getLogger(__name__)


class CheckMasterLocationTest(unittest.TestCase):

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
        self.mock.setUp(__file__, nodes=2)

    def tearDown(self):
        """ 
        Finish all services started for simulation. 
        """ 
        self.mock.tearDown()

    @pytest.mark.timeout(300, method='thread')
    def test(self):
        """Test. note that all test method names must begin with 'test.'"""
        """WARNING: IT IS HIGHLY RECOMMENDED TO HAVE ONE TEST ONLY TO ISOLATE FUNCTIONAL TESTS FROM EACH OTHER. i.e. 
        Start a new Python Interpreter and JVM for each test. In the end, it means only one test in this class. """
        from dataclay.api import init

        logger.debug('**Starting init**')
        init()
        
        """ 
        Imports. Imports must be located here in order to simulate "import" order in a real scenario. 
        VERY IMPORTANT: Imports must be located AFTER init
        """
        from model.classes import Person
        from dataclay.commonruntime.Runtime import getRuntime
        self.session_initialized = True
    
        """
        Test. From now on, the Functional Test itself. 
        """
        p = Person('foo', 100)

        execution_environments = list(getRuntime().get_execution_environments_info().keys())

        self.assertTrue(len(execution_environments) > 1) 

        p.make_persistent(backend_id=execution_environments[0])

        p.new_replica(backend_id=execution_environments[1])
        
        self.assertEqual(p.run_remote(execution_environments[0], 'getMyMasterLocation', None), execution_environments[0])
        self.assertEqual(p.run_remote(execution_environments[1], 'getMyMasterLocation', None), execution_environments[0])
        
        logger.debug("Test OK!")
