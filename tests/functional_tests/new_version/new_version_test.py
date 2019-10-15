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
NewVersion testing. 
"""
logger = logging.getLogger(__name__)


class NewVersionTest(unittest.TestCase):

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
        from model.classes import Person
        
        self.session_initialized = True
    
        """
        Test. From now on, the Functional Test itself. 
        """

        # Test makePersistent
        person = Person(name='Nikola', age=86)
        person.make_persistent(alias="Tesla")
        
        self.assertTrue(person.is_persistent())

        # Test NewVersion
        version_info, unloaded_version_info = person.new_version(list(person.get_all_locations().keys())[0])
        logger.debug("Version info are:\n%s", version_info)
        versionOID = version_info.versionOID

        person_version = Person.get_object_by_id(versionOID)
        logger.debug("New version of person is:\n%s", person_version)

        # NewVersion name and age are the same of the original
        self.assertEqual(person.name, person_version.name) 
        self.assertEqual(person.age, person_version.age)

        # NewVersion ID is different
        self.assertNotEqual(person.get_object_id(), person_version.get_object_id())
        
        logger.debug("Test OK!")
