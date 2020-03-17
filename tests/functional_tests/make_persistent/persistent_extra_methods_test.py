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


class MakePersistentExtraMethodsTest(unittest.TestCase):

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
        from model.classes import FancyUUMethods
        
        self.session_initialized = True
    
        # Test. From now on, the Functional Test itself.

        o = FancyUUMethods(42, "Hello World")

        self.assertEqual("%s" % o, "Message[42]: Hello World")

        o.make_persistent()

        self.assertEqual("%s" % o, "Message[42]: Hello World")

        p = FancyUUMethods(42, "Not Hello World")
        q = FancyUUMethods(43, "Hello World")
        p.make_persistent("p_obj")
        q.make_persistent("q_obj")

        self.assertEqual(o, p)
        self.assertNotEqual(o, q)
        self.assertNotEqual(p, q)

        p_bis = FancyUUMethods.get_by_alias("p_obj")
        q_bis = FancyUUMethods.get_by_alias("q_obj")

        self.assertEqual(o, p_bis)
        self.assertNotEqual(o, q_bis)
        self.assertNotEqual(p_bis, q_bis)

        s = set()
        s.add(o)
        self.assertEqual(len(s), 1)
        s.add(p_bis)  # this won't add an object because o == p
        self.assertEqual(len(s), 1)
        s.add(q_bis)
        self.assertEqual(len(s), 2)

        self.assertIn(o, s)
        self.assertIn(p, s)  # this works because o == p
        self.assertIn(q, s)

        logger.debug("Test OK!")
