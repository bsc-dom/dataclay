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
import resource
import time
import gc
import sys
from unittest.case import SkipTest
import logging
import pytest
import traceback
from multiprocessing import Process, Queue
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
        """
        PyUnit function called before every test case.
        Starts DataClay simulation in one Python interpreter and one Java VM. This allows us to Debug in a local machine without 
        dockers and without a full start of DataClay (jars, configurations, ...) 
        """ 
        Configuration.MEMMGMT_PRESSURE_FRACTION = 0.01
        self.mock.setUp(__file__)

    def tearDown(self):
        """ 
        Finish all services started for simulation. 
        """ 
        self.mock.tearDown()
        
    def client_process1(self, q):
        try:
            from dataclay.api import init, finish
            logger.debug('**Starting init 1**')
            init()
            
            """ 
            Imports. Imports must be located here in order to simulate "import" order in a real scenario. 
            VERY IMPORTANT: Imports must be located AFTER init
            """
            from model.classes import WebSite, WebPage, URI
        
            """
            Test. From now on, the Functional Test itself. 
            """
            web_sites_ids_str = list()
            for i in range(0, 10):
                alias = "bsc%s" % str(i);
                web_site = WebSite(alias)
                try:
                    web_site.make_persistent(alias=alias)
                except:
                    traceback.print_exc()
                web_sites_ids_str.append(str(web_site.get_object_id()))
            
            finish()
            q.put(["OK", web_sites_ids_str])
        except: 
            q.put("FAIL")
            
    def client_process2(self, q, web_sites_ids_str):
        try:
            from dataclay.api import init, finish
            logger.debug('**Starting init 2 **')
            init()
            """ 
            Imports. Imports must be located here in order to simulate "import" order in a real scenario. 
            VERY IMPORTANT: Imports must be located AFTER init
            """
            from model.classes import WebSite, WebPage, URI
            
            for i in range(0, 10):
                web_site_2 = WebSite.get_by_alias("bsc%s" % str(i))
                self.assertEqual(web_sites_ids_str[i], str(web_site_2.get_object_id()))
               
            finish()
            q.put("OK")
        except: 
            q.put("FAIL")
        
    @pytest.mark.timeout(1000, method='thread')
    def test(self):
        """Test. note that all test method names must begin with 'test.'"""
        """WARNING: IT IS HIGHLY RECOMMENDED TO HAVE ONE TEST ONLY TO ISOLATE FUNCTIONAL TESTS FROM EACH OTHER. i.e. 
        Start a new Python Interpreter and JVM for each test. In the end, it means only one test in this class. """
        logger.info('**Starting test**')
        q = Queue()

        p = Process(target=self.client_process1, args=(q,))
        p.start()
        result = q.get()
        p.join()
        self.assertEqual(result[0], "OK")  
        web_sites_ids_str = result[1]
        logger.debug("Restarting dataClay")
        self.mock.mock.restartDataClay()
        p = Process(target=self.client_process2, args=(q, web_sites_ids_str))
        p.start()
        result = q.get()
        p.join()
        self.assertEqual(result, "OK")  
        logger.info("** Test OK!")
