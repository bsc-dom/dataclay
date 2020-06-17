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
Types testing. 
"""
logger = logging.getLogger(__name__)


class TypesTest(unittest.TestCase):

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
        from model.classes import Player, Carrer
        from dataclay import getRuntime
        from dataclay.DataClayObjProperties import DCLAY_GETTER_PREFIX

        self.session_initialized = True
    
        """
        Test. From now on, the Functional Test itself. 
        """
        environments_ids = list(getRuntime().get_execution_environments_info().keys())
        environment1_id = environments_ids[0]
        environment2_id = environments_ids[1]

        messi = Player("Leo", "Messi", 30)
        
        messi.add_role("forward")
        messi.add_skill("dribbling")
        
        messi_carrer = Carrer()

        stats_2016_2017 = dict()
        stats_2016_2017["goal"] = 54
        stats_2016_2017["presence"] = 52

        messi_carrer.add_stat("2016/2017", stats_2016_2017)

        messi_carrer.add_team("2016/2017", "Barcelona FC")

        messi.add_carrer(messi_carrer)
        
        messi.add_test_types(True, 2, "Str")

        messi.make_persistent(backend_id=environment1_id)

        self.assertTrue(messi.is_persistent)
        self.assertTrue(messi.carrer.is_persistent)

        messi.new_replica(backend_id=environment2_id)
        
        # Updates locations after replication
        messi_locations = messi.get_all_locations()
        messi_carrer_locations = messi.carrer.get_all_locations()

        # Check that object is replicated
        self.assertEqual(len(messi_locations), 2)
        self.assertIn(environment1_id, messi_locations)
        self.assertIn(environment2_id, messi_locations)

        # Check that associated objects are replicated
        self.assertIn(environment2_id, messi_carrer_locations)

        replicated_messi_carrer = messi.run_remote(environment2_id, DCLAY_GETTER_PREFIX + 'carrer', None)
        replicated_messi_teams = replicated_messi_carrer.run_remote(environment2_id, DCLAY_GETTER_PREFIX + 'teams', None)
        replicated_messi_stats = replicated_messi_carrer.run_remote(environment2_id, DCLAY_GETTER_PREFIX + 'stats', None)

        self.assertEqual(messi.carrer.teams, replicated_messi_teams)
        self.assertEqual(messi.carrer.stats, replicated_messi_stats)
        logger.info("Messi replicated stats are %s", replicated_messi_stats)

        logger.debug("Test OK!")
