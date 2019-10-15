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
Volatiles testing. 
"""
logger = logging.getLogger()


class RemoteGetterTestCase(unittest.TestCase):

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
        self.mock.setUp(__file__, nodes=2)

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
        from model.classes import WebSite, WebPage
        from dataclay import getRuntime
        self.session_initialized = True
    
        """
        Test. From now on, the Functional Test itself. 
        """

        execs_info = getRuntime().get_execution_environments_info()
        
        exec_env_info_1 = execs_info[list(execs_info.keys())[0]]
        exec_env_info_2 = execs_info[list(execs_info.keys())[1]]
        
        host = "bsc.es"
        web_site = WebSite(host)
        web_site.make_persistent(alias=web_site.uri.host, backend_id=exec_env_info_1.dataClayID)
            
        web_page = WebPage(host + "/page.html")  
        web_page.make_persistent(backend_id=exec_env_info_2.dataClayID) 
        
        web_site.add_web_page(web_page)
        
        self.assertTrue(web_site.is_persistent()) 
        self.assertTrue(web_site.uri.is_persistent())
        self.assertTrue(web_page.is_persistent())  # volatile is persistent
        self.assertTrue(web_page.uri.is_persistent())  # volatile is persistent
        
        logger.debug("Test OK!")
