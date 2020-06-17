from __future__ import absolute_import
""" Class description goes here. """

""" 
Use absolute imports. By default, when you import a package in Python 2, it adds '.' in the beggining, it means all 
imports are relative. It's a problem for our testing since our test can be in a package but our stubs are not including 
the package of the test (and shouldn't!). With __future__ we add Python 3 functionality for all imports to be absolute. 
"""
# Initialize dataClay
from mock.simplemock import SimpleMock
from dataclay.heap import ExecutionEnvironmentHeapManager
import unittest 
import os
import resource
import time
import gc
import sys
from unittest.case import SkipTest
import logging
import pytest
from dataclay.util import Configuration

"""
Memory testing. 
"""
logger = logging.getLogger(__name__)


class GCUpdateTestCase(unittest.TestCase):

    """
    DataClayMock object for simulation. 
    """
    
    mock = SimpleMock() 
    
    def setUp(self):
        """ To force GC, hack memory pressure """

        # ToDo: the (...).Configuration is extremely ugly and completely useless
        # ToDo: @abarcelo I left it like that because I did not understand previous
        # ToDo: ExecutionEnvironmentHeapManager.GC_MEMORY_... usage
        Configuration.MEMMGMT_PRESSURE_FRACTION = 0.01
        
        rsrc = resource.RLIMIT_AS
        soft, hard = resource.getrlimit(rsrc)
        logger.debug('Soft limit starts as  :%s', soft)
        logger.debug('Hard limit starts as  :%s', hard)

        kb = 1024
        mb = 1024 * kb
        gb = 1024 * mb
        # resource.setrlimit(rsrc, (-1, hard)) 
        
        soft, hard = resource.getrlimit(rsrc)
        logger.debug('Soft limit changed to :%s', soft)
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
        web_site = WebSite(host + "/foo/bsc.html")
        web_site.make_persistent(alias=web_site.uri.host)
            
        cur_host = "volatile_web"
        web_page = WebPage(cur_host)
        logger.debug("web page oid = %s", web_page.get_object_id())
        logger.debug("uri oid = %s", web_page.uri.get_object_id())
        web_site.add_web_page(web_page)
        
        """ Sleep enough time to allow GC action """
        print("Waiting for GC action...")
        time.sleep(5)
        
        """ Modify web page """ 
        web_page.uri.host = "new_volatile_web"
        
        """ Sleep enough time to allow GC action """
        print("Waiting for GC action...")
        time.sleep(5)
        
        """ Get web page """ 
        self.assertEquals(web_page.uri.host, "new_volatile_web")
        
        logger.debug("Test OK!")
