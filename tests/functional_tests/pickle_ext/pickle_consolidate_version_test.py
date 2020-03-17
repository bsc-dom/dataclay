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
Consolidate2 testing. 
"""


class PickleConsolidateTest(unittest.TestCase):

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
        from dataclay.api import logger
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

        # Add web_page to web_site and make it persistent
        web_site.add_web_page(web_page)
        self.assertIs(web_page, web_site.pages[0])
        web_site.make_persistent()

        self.assertTrue(web_site.is_persistent()) 
        self.assertEqual(len(web_site.get_all_locations()), 1)
        self.assertTrue(web_site.uri.is_persistent())
        self.assertEqual(len(web_site.uri.get_all_locations()), 1)

        # NewVersion for WebSite
        version_info, unloaded_version_info = web_site.new_version(list(web_site.get_all_locations().keys())[0])
        logger.debug(version_info)
        versionOID = version_info.versionOID
        web_site_version = WebSite.get_object_by_id(versionOID)

        self.assertNotEqual(web_site.get_object_id(), web_site_version.get_object_id())
        self.assertTrue(web_site_version.is_persistent())
        self.assertEqual(len(web_site_version.get_all_locations()), 1)
        self.assertTrue(web_site_version.uri.is_persistent())
        self.assertEqual(len(web_site_version.uri.get_all_locations()), 1)

        web_page_version = web_site_version.pages[0]

        self.assertEqual(len(web_site_version.pages), 1)
        self.assertNotEqual(web_page.get_object_id(), web_page_version.get_object_id())
        self.assertNotEqual(web_page, web_page_version)

        # Add A new WebPage to WebSite version pages
        new_web_page = WebPage(host + "/page2.html")
        # FIXME: NewPage is consolidated just if is maked Persistent before
        new_web_page.make_persistent()
        web_site_version.add_web_page(new_web_page)
        self.assertEqual(len(web_site_version.pages), 2)

        # Consolidate and check that page is also added to new one
        logger.debug("Original oid: %s", web_site.get_object_id()) 
        web_site.consolidate_version(unloaded_version_info)
        
        logger.debug("Original oid: %s", web_site.get_object_id()) 
        self.assertEqual(len(web_site.pages), 2)
        
        logger.debug("Test OK!") 
