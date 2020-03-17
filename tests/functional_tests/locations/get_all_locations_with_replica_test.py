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
GetAllLocationWithReplica testing. 
"""
logger = logging.getLogger(__name__)


class GetAllLocationWithReplicaTest(unittest.TestCase):

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
        from model.classes import WebSite, WebPage, URI
        from dataclay import getRuntime
        self.session_initialized = True
    
        """
        Test. From now on, the Functional Test itself. 
        """

        host = "bsc.es"
        web_site = WebSite(host)

        environments_ids = list(getRuntime().get_execution_environments_info().keys())
        self.assertEqual(len(environments_ids), 2)
        environment1_id = environments_ids[0]
        environment2_id = environments_ids[1]

        # MakePersistent in location1        
        web_site.make_persistent(backend_id=environment1_id)
        web_site.new_replica(backend_id=environment2_id, recursive=True)

        object_id = web_site.get_object_id()
        all_locations_ids = web_site.get_all_locations().keys()

        self.assertTrue(web_site.is_persistent())
        self.assertIsNotNone(object_id)
        
        # All_locations contains environment1_id and environment2_id
        self.assertIn(environment1_id, all_locations_ids)
        self.assertIn(environment2_id, all_locations_ids)
        self.assertEqual(len(all_locations_ids), 2)
        logger.debug("Test OK!")
