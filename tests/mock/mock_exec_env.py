
""" Class description goes here. """

import multiprocessing 
import os
import time
import logging
import gc

logger = logging.getLogger(__name__)


class MockExecutionEnvironment(multiprocessing.Process):

    def __init__(self, sl_id, ee_id, queue, configurer, lm_port, initial_port):
        multiprocessing.Process.__init__(self)
        self.ds_name = "DS%s" % str(sl_id)  # Name refers to storage location name
        self.node_id = "EE%s_%s" % (sl_id, ee_id)
        self.queue = queue 
        self.configurer = configurer
        self.exec_env_srv = None
        self.lm_port = lm_port
        self.port = initial_port
        self.daemon = True
        self.name = self.node_id

    def run(self):
        
        ### Set environment variables for Execution Environment #### 
        os.environ["LOGICMODULE_HOST"] = "localhost"
        os.environ["LOGICMODULE_PORT_TCP"] = str(self.lm_port)
        os.environ["DATASERVICE_NAME"] = self.ds_name
        os.environ["DEPLOY_PATH"] = "/tmp/pythonee" + self.node_id
        os.environ["DEPLOY_PATH_SRC"] = "/tmp/pythonee" + self.node_id + "/src"
        # os.environ['DATACLAY_LOGGING_CONFIG'] = os.path.dirname(os.path.abspath(__file__)) + "/log_config.yaml"
        os.environ["DATASERVICE_PYTHON_PORT_TCP"] = str(self.port)
        self.configurer(self.queue)
        logger.debug('**[PythonMockDataClay]** Starting Execution Environment ' + self.node_id)
        
        # Import here to take into account env variables!
        from dataclay.executionenv.server.__main__ import run_main
        run_main()
        gc.collect() 
