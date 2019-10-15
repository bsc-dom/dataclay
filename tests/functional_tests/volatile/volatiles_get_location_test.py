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
volatilesGetLocation testing. 
"""
logger = logging.getLogger(__name__)


class volatilesGetLocationTest(unittest.TestCase):

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
        from dataclay import getRuntime        
        self.session_initialized = True
    
        """
        Test. From now on, the Functional Test itself. 
        """

        host = "bsc.es"
        web_page = WebPage(host + "/foo/bsc.html")
        web_page.make_persistent(alias=web_page.uri.host)
            
        host = "fsf.org"
        web_site = WebSite(host)
        web_site.add_web_page(web_page)  # added persistent object to a volatile 
                
        web_page.add_link(web_site)  # send volatile
                
        self.assertTrue(web_site.is_persistent())
        self.assertTrue(web_site.uri.is_persistent())
        self.assertTrue(web_page.is_persistent())
        self.assertTrue(web_page.uri.is_persistent())

        object_id = web_site.get_object_id()
        backend_id = web_site.get_location()

        # Assert that backend_id of volatile object is the hint
        self.assertIsNotNone(object_id)
        self.assertEqual(backend_id, web_site.get_hint())

        logger.debug("Test OK!")
