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
ConsolidateVersion testing. 
"""
logger = logging.getLogger(__name__)


class ConsolidateVersionTest(unittest.TestCase):

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

        # Create newVersion and change name and age of it
        for k, v in person.get_all_locations().items():
            version_info, unloaded_version_info = person.new_version(k)

        versionOID = version_info.versionOID

        person_version = Person.get_object_by_id(versionOID)
        
        person_version.name = "Thomas"
        person_version.age = 84

        # Test ConsolidateVersion
        person.consolidate_version(unloaded_version_info)

        # Check that fields are consolidated
        self.assertEqual(person.name, "Thomas")
        self.assertEqual(person.age, 84) 
        self.assertEqual(Person.get_by_alias("Tesla").name, "Thomas")
        self.assertEqual(Person.get_by_alias("Tesla").age, 84) 
        logger.debug("After Consolidate, new name: %s and new age: %s", person.name, person.age)

        logger.debug("Test OK!") 
