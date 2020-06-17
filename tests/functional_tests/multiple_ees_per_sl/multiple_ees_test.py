from __future__ import absolute_import
""" Class description goes here. """

""" 
Use absolute imports. By default, when you import a package in Python 2, it adds '.' in the beggining, it means all 
imports are relative. It's a problem for our testing since our test can be in a package but our stubs are not including 
the package of the test (and shouldn't!). With __future__ we add Python 3 functionality for all imports to be absolute. 
"""
# Initialize dataClay
from mock.mockdataclay import MockDataClay
import unittest 
import os
import logging
import pytest
import traceback

"""
GetLocation testing. 
"""
logger = logging.getLogger(__name__)


class MultipleEEsTest(unittest.TestCase):

    """ Python mock dataclay """
    mock = None
    """ Mock dataclay Java instance."""
    java_mock_dataclay = None 
    """ Mock consumer."""
    consumer = None 
    """ Number of nodes."""
    num_nodes = 1
    """ Number of EEs per node. """
    num_ees_per_sl = 4

    def setUp(self):
        """
        PyUnit function called before every test case.
        Starts DataClay simulation in one Python interpreter and one Java VM. This allows us to Debug in a local machine without 
        dockers and without a full start of DataClay (jars, configurations, ...) 
        """ 
        try:
            self.session_initialized = False
            self.mock = MockDataClay(self.num_nodes, ees_per_sl=self.num_ees_per_sl) 
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
        if self.session_initialized:
            from dataclay.api import finish
            finish()
        self.mock.finishSimulation()
        logger.debug("Finished tear down of test")

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
        self.assertEqual(len(environments_ids), 4)
        
        environment1_id = environments_ids[0]

        # MakePersistent in location1        
        web_site.make_persistent(backend_id=environment1_id)
        object_id = web_site.get_object_id()
        backend_id = web_site.get_location()

        # Assert that backend_id of persistent object is environment1
        self.assertTrue(web_site.is_persistent())
        self.assertIsNotNone(object_id)
        self.assertEqual(backend_id, environment1_id)
        
        # Create replicas in all EEs
        web_site.new_replica(backend_id=environments_ids[1])
        web_site.new_replica(backend_id=environments_ids[2])
        web_site.new_replica(backend_id=environments_ids[3])
        
        logger.debug("Test OK!")
