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

"""
Memory testing. 
"""
logger = logging.getLogger(__name__)


class VolatileMapRestartTest(unittest.TestCase):

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
        
    def client_process1(self, q):
        try:
            from dataclay.api import init, finish
    
            logger.info('**Starting init 1**')
            init()
            
            """ 
            Imports. Imports must be located here in order to simulate "import" order in a real scenario. 
            VERY IMPORTANT: Imports must be located AFTER init
            """
            from model.classes import Mapa, Node
            self.session_initialized = True
        
            """
            Test. From now on, the Functional Test itself. 
            """
            
            try:
                m = Mapa.get_by_alias("mapa")
                logger.info("Already in the DB")
                    
            except Exception:
                m = Mapa()
                m.make_persistent(alias="mapa")
                logger.info("Not found, creating Mapa and making it persistent")
                
            # Node with current location added by jetson
            # it should be done with get_current_location() in order to get pos1 and pos2
            n = Node(1, 1, 1, 1.5, 1.5)
            n.make_persistent()
            m.add(n)
            print("NODE created and added to Mapa")
            time.sleep(5)
            
            finish()
            
            q.put("OK")
        except: 
            q.put("FAIL")
            
    def client_process2(self, q):
        try:
            from dataclay.api import init, finish
            logger.info('**Starting init 2**')
            init()
            
            """ 
            Imports. Imports must be located here in order to simulate "import" order in a real scenario. 
            VERY IMPORTANT: Imports must be located AFTER init
            """
            from model.classes import Mapa, Node
            self.session_initialized = True
        
            """
            Test. From now on, the Functional Test itself. 
            """
            m = Mapa.get_by_alias("mapa")
            logger.info("Map obtained ")
            mapa = m.mapa
            logger.info("** Getter of mapa done with num elements: %s" % str(len(mapa)))
            for nid, node in mapa.items():
                logger.info("** Found node %s" % str(nid))
            
            finish()
            
            q.put("OK")
        except: 
            q.put("FAIL")
            
    @pytest.mark.timeout(500, method='thread')
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
        self.assertEqual(result, "OK")  
        logger.debug("Restarting dataClay")
        self.mock.mock.restartDataClay()
        p = Process(target=self.client_process2, args=(q,))
        p.start()
        result = q.get()
        p.join()
        self.assertEqual(result, "OK")  

        logger.info("** Test OK!")
