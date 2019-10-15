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
import pytest

"""
MakePersistent testing. 
"""
logger = logging.getLogger(__name__)


class MakePersistentTest(unittest.TestCase):

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
        from model.classes import WebSite, WebPage, URI
        
        self.session_initialized = True
    
        """
        Test. From now on, the Functional Test itself. 
        """

        host = "bsc.es"
        web_site = WebSite(host)
        web_page = WebPage(host + "/page.html")
        web_page2 = WebPage(host + "/page2.html")

        # Verify object_iD is not null
        object_id = web_site.get_object_id()

        self.assertTrue(object_id != None)

        web_site.add_web_page(web_page)

        self.assertEqual(len(web_site.pages), 1)
        # Test make_persistent

        web_site.make_persistent(recursive=False)
        
        self.assertTrue(web_site.is_persistent())
        
        # TODO: Test better this
        # Add another page after persistence but web_site.uri.host is not persistent
        # (See add_we_page method in model/classes.py)
        self.assertRaises(Exception, web_site.add_web_page, web_page2) 
          
        logger.debug("Test OK!")
