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
        self.mock.setUp(__file__)

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
        
        self.session_initialized = True
    
        """
        Test. From now on, the Functional Test itself. 
        """

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

        messi.make_persistent()

        self.assertTrue(messi.is_persistent)
        self.assertTrue(messi.carrer.is_persistent)

        # Test NewVersion
        version_info, unloaded_version_info = messi.new_version(list(messi.get_all_locations().keys())[0])
        logger.debug("Version info are:\n%s", version_info)
        versionOID = version_info.versionOID

        messi_version = Player.get_object_by_id(versionOID)
        logger.debug("New version of messi is:\n%s", messi_version)

        # NewVersion ID is different
        self.assertNotEqual(messi.get_object_id(), messi_version.get_object_id())

        # NewVersion fields are the same of the original
        self.assertEqual(messi.a, messi_version.a)
        self.assertEqual(messi.b, messi_version.b)
        self.assertEqual(messi.c, messi_version.c)
        self.assertEqual(messi.skills, messi_version.skills)
        self.assertEqual(messi.roles, messi_version.roles)
        self.assertEqual(messi.personal_info, messi_version.personal_info)
        self.assertEqual(messi.carrer.teams, messi_version.carrer.teams)
        self.assertEqual(messi.carrer.stats, messi_version.carrer.stats) 

        stats_2015_2016 = dict()
        stats_2015_2016["goal"] = 41
        stats_2015_2016["presence"] = 49

        messi_version.carrer.add_team("2015/2016", "Barcelona FC")
        messi_version.carrer.add_stat("2015/2016", stats_2015_2016)

        self.assertNotEqual(messi.carrer.stats, messi_version.carrer.stats)
        self.assertNotEqual(messi.carrer.teams, messi_version.carrer.teams)
        self.assertEqual(len(messi.carrer.teams), 1)
        self.assertEqual(len(messi_version.carrer.teams), 2)
        self.assertEqual(len(messi.carrer.stats), 1)
        self.assertEqual(len(messi_version.carrer.stats), 2)
        
        messi.consolidate_version(unloaded_version_info)        
        
        self.assertEqual(len(messi.carrer.teams), 2)
        self.assertEqual(len(messi.carrer.stats), 2)

        logger.debug("Test OK!")
