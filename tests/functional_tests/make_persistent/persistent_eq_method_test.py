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
MakePersistent testing. 
"""
logger = logging.getLogger(__name__)


class MakePersistentWithStrMethodTest(unittest.TestCase):

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
        # WARNING: IT IS HIGHLY RECOMMENDED TO HAVE ONE TEST ONLY TO ISOLATE FUNCTIONAL TESTS FROM EACH OTHER. i.e.
        # Start a new Python Interpreter and JVM for each test. In the end, it means only one test in this class.
        from dataclay.api import init

        logger.debug('**Starting init**')
        init()

        # Imports. Imports must be located here in order to simulate "import" order in a real scenario.
        # VERY IMPORTANT: Imports must be located AFTER init
        from model.classes import HasEqMethod
        
        self.session_initialized = True
    
        # Test. From now on, the Functional Test itself.

        o = HasEqMethod(1)
        p = HasEqMethod(1)
        q = HasEqMethod(1)
        r = HasEqMethod(2)

        self.assertEqual(o, p)
        self.assertEqual(o, q)
        self.assertNotEqual(o, r)

        o.make_persistent()
        # This is triggering something like p == o, which doesn't matter
        self.assertEqual(p, o)
        # This is triggering something like o == q,
        # which will remote call the __eq__ method on a persistent object (o object)
        # which will trigger q to become a volatile
        # which will as a matter of act make q persistent (not exactly, but close)
        self.assertEqual(o, q)

        p.make_persistent("alias_p")
        # q was persistent , so this silently fails, no alias associated
        q.make_persistent("alias_q")
        r.make_persistent("alias_r")

        self.assertEqual(o, p)
        self.assertEqual(o, q)
        self.assertNotEqual(o, r)

        p_bis = HasEqMethod.get_by_alias("alias_p")
        # this fails because q has not been assigned an alias
        q_bis = HasEqMethod.get_by_alias("alias_q")
        r_bis = HasEqMethod.get_by_alias("alias_r")

        self.assertEqual(o, p_bis)
        self.assertEqual(o, q_bis)
        self.assertNotEqual(o, r_bis)

        logger.debug("Test OK!")
