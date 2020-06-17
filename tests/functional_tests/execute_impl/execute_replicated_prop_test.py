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
ExecuteReplicatedProperties testing. 
"""
logger = logging.getLogger(__name__)


class ExecuteReplicatedPropertiesTest(unittest.TestCase):

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
        from model.replication_class import Person
        from dataclay import getRuntime
        from dataclay.exceptions.exceptions import DataClayException

        self.session_initialized = True
    
        """
        Test. From now on, the Functional Test itself. 
        """
        environments_ids = list(getRuntime().get_execution_environments_info().keys())
        environment1_id = environments_ids[0]

        self.assertEqual(len(environments_ids), 2) 

        # When we create a Person object we call the locally set for non-persistent object.__setattr__
        p = Person('foo', 100)
        r = Person('fat', 200)

        p.make_persistent(backend_id=environment1_id)
        r.make_persistent(backend_id=environment1_id)
        
        self.assertEqual(p.get_master_location(), environment1_id)

        # name is a replicated attribute so the before method should be called before the setter
        # When we change the name we call a inMaster setter execute_implementation_aux('__setUpdate__', ...)
        p.name = 'aaa'

        # When we change the age we call a remote __setUpdate__ on object
        r.age = 78
        self.assertEqual(r.age, 78)

        # Assert that the attribute was properly changed
        self.assertEqual(p.name, 'aaa')

        # Check that before method was called
        self.assertEqual(p.years, 3)
        
        logger.debug("Test OK!")
