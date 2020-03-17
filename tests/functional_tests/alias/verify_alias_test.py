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
VerifyAlias testing. 
"""
logger = logging.getLogger(__name__)


class VerifyAliasTest(unittest.TestCase):

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
        from dataclay import getRuntime
        from dataclay.commonruntime.Settings import settings

        self.session_initialized = True
    
        """
        Test. From now on, the Functional Test itself. 
        """
        lm_client = getRuntime().ready_clients["@LM"]
        alias = "test_alias"

        # Test make_persistent
        person = Person(name='Nikola', age=86)
        person.make_persistent(alias)
        
        # Verify object_iD is not null
        object_id = person.get_object_id()

        self.assertTrue(object_id != None)
        # check you can get person by alias without exception
        Person.get_by_alias(alias=alias)

        # Verify that object is in DB/Cache/Metadata
        # TODO: Missing the check on DB

        metadata = lm_client.get_metadata_by_oid(settings.current_session_id, object_id)
        alias_cache = getRuntime().alias_cache

        self.assertIn(alias, metadata.aliases)
        self.assertIn(alias, alias_cache)
  
        # Test delete_alias
        Person.delete_alias(alias)
        self.assertRaises(Exception, Person.get_by_alias, alias=alias)

        # Verify that object is not in DB/Cache/Metadata
        metadata = lm_client.get_metadata_by_oid(settings.current_session_id, object_id)
        alias_cache = getRuntime().alias_cache

        self.assertNotIn(alias, metadata.aliases)
        self.assertNotIn(alias, alias_cache)

        logger.debug("Test OK!")
