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
        
        logger.info("PLAYER %s , ROLES: %s AND SKILLS: %s", messi.personal_info, messi.roles, messi.skills)

        logger.info("PLAYER %s , WITH CARRER STATS %s", messi.personal_info, messi.carrer.stats)

        logger.info("PLAYER %s , PLAYED IN %s", messi.personal_info, messi.carrer.teams)
        
        d = set()
        d.add(1)
        d.add(2)

        messi.add_test_types(True, 2, "Str", d)

        messi.make_persistent()

        self.assertTrue(messi.is_persistent)
        self.assertTrue(messi.carrer.is_persistent)

        logger.info("PLAYER %s , ROLES: %s AND SKILLS: %s", messi.personal_info, messi.roles, messi.skills)

        logger.info("PLAYER %s , WITH CARRER STATS %s", messi.personal_info, messi.carrer.stats)
        
        logger.info("PLAYER %s , PLAYED IN %s TYPE %s", messi.personal_info, messi.carrer.teams, type(messi.carrer.teams[0]))

        logger.info("TEST TYPES %s %s, %s %s, %s %s, %s %s", type(messi.a), messi.a, type(messi.b), messi.b, type(messi.c), messi.c, type(messi.d), messi.d)

        logger.debug("Test OK!")
