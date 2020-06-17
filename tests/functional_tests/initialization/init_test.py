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
Initialization testing. 
"""
logger = logging.getLogger(__name__)


class InitializationTest(unittest.TestCase):

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

    @unittest.skip("skipping test because get_execution_environments_per_locations_for_ds is deprecated")
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
        from dataclay import getRuntime
        from dataclay.communication.grpc.messages.common.common_messages_pb2 import LANG_PYTHON, LANG_JAVA
        from dataclay.commonruntime.Settings import settings

        self.session_initialized = True
    
        """
        Test. From now on, the Functional Test itself. 
        """

        lm_client = getRuntime().ready_clients["@LM"]

        python_ees_info = lm_client.get_execution_environments_info(settings.current_session_id, LANG_PYTHON)
        java_ees_info = lm_client.get_execution_environments_info(settings.current_session_id, LANG_JAVA)

        #### WARNING!!!!! get_execution_environments_per_locations_for_ds DEPRECATED!
        python_ee_per_loc_for_ds = lm_client.get_execution_environments_per_locations_for_ds(LANG_PYTHON)
        java_ee_per_loc_for_ds = lm_client.get_execution_environments_per_locations_for_ds(LANG_JAVA)

        # Check that EEs are correctly initialized and assigned to the right SL 

        for py_ee in python_ees_info:
            self.assertNotIn(py_ee, java_ees_info.values())
            self.assertIn(py_ee, python_ee_per_loc_for_ds.values())
            self.assertNotIn(py_ee, java_ee_per_loc_for_ds.values())
        
        for java_ee in java_ees_info:
            self.assertNotIn(java_ee, python_ees_info.values())
            self.assertIn(java_ee, java_ee_per_loc_for_ds.values())
            self.assertNotIn(java_ee, python_ee_per_loc_for_ds.values())

        logger.debug("Test OK!")
