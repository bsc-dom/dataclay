
""" Class description goes here. """

import fnmatch
import jpype
import os
import multiprocessing
import time
import logging 
import psutil
import signal
import traceback
import subprocess
import shlex
import shutil
from multiprocessing import Process, Queue

logger = logging.getLogger()


class MockDataClay(object):
    
    def __init__(self, num_nodes, ees_per_sl=1):
        
        cfg_files_path = os.path.dirname(os.path.abspath(__file__)) + "/cfgfiles/global.properties"
        os.environ["DATACLAYGLOBALCONFIG"] = cfg_files_path
        separator = "="
        with open(cfg_files_path) as f:
            for line in f:
                if separator in line:
                    # Find the name and value by splitting the string
                    name, value = line.strip().split(separator, 1)
                    print("Found configuration %s = %s" % (name, value))
                    if name == "CHECK_LOG4J_DEBUG":
                        print("DEBUG IS %s" % value)
                        if value == "true" or value == "True":
                            os.environ['DEBUG'] = "True"
        self.mock_dataclay = None  # Gateway to Java classes
        self.num_execenvs = 0  # Number of execution environments
        self.exec_envs = list() 
        """ === Logging ==== """
        self.log_listener = None  # Log listener process
        self.multiprocess_queue = None
        """ ======= """
        self.num_execenvs = num_nodes
        self.cur_lm_port = 1034
        self.num_storagelocs = num_nodes
        self.ees_per_sl = ees_per_sl

    def run_command(self, command, working_dir):
        process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, cwd=working_dir)
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        rc = process.poll()
        return rc
    
    def findProcess(self):
        """
        WARNING: USE IT CAREFULLY. This function is intended to cotnrol if there is another python test running (due 
        to some aborted built, stack threads, ..."
        """
        ps = subprocess.Popen("ps -ef | grep pytest | grep functional_tests | grep <pid> | grep -v grep", shell=True, stdout=subprocess.PIPE)
        output = ps.stdout.read()
        ps.stdout.close()
        ps.wait()
        return output
    
    def kill_pytest_processes(self):
        try:
            
            current_pid = os.getpid()
            parent_pid = os.getppid()
            logger.debug("Current pid: %s" % str(current_pid))
            logger.debug("Parent pid: %s" % str(parent_pid))
            for pid in psutil.pids():
                p = psutil.Process(pid)
                if p.name() == "pytest" and pid != current_pid and pid != parent_pid:
                    logger.debug("Killing Pytest process %s" % str(pid))
                    logger.debug(str(p.cmdline()))
                    p.kill()
            
                if p.name() == "python" and pid != current_pid and pid != parent_pid:
                    for param in p.cmdline():
                        if "pydev" in param and "functional_tests" in param:
                            logger.debug("Killing pytest (via PyDev) process %s" % str(pid))
                            logger.debug(str(p.cmdline()))
                            p.kill()
                            break
                    
        except:
            traceback.print_exc()

    def startJavaMockDataClay(self):
        # WARNING: DataClay class path is RELATIVE!
        project_path = os.path.dirname(os.path.abspath(__file__)) + "/../../../"

        """
        Check if .class file exists. Otherwise, compile Java code 
        """ 
        print("**[PythonMockDataClay]** Checking if dataClay java is compiled.")
        gw_class_file = project_path + "/target/test-classes/mock/MockPythonGateway.class"
        if not os.path.isdir(project_path + "/target/classes") or not os.path.isfile(gw_class_file):
            raise SystemError("**[PythonMockDataClay]** DataClay Java is not compiled in %s/target/classes folder. Please compile it!" % project_path)
        if not os.path.isdir(project_path + "/target/test-classes") or not os.path.isfile(gw_class_file):
            raise SystemError("**[PythonMockDataClay]** DataClay Java is not compiled in %s/target/test-classes folder. Please compile it!" % project_path)
        if not os.path.isdir(project_path + "/lib"):
            raise SystemError("**[PythonMockDataClay]** Cannot find any library in %s/lib folder, please copy them." % project_path)
        if os.path.isdir(project_path + "/lib") and not os.listdir(project_path + "/lib"):
            raise SystemError("**[PythonMockDataClay]** DataClay Java is not compiled. Please compile it!")
          
        classpath = "-Djava.class.path=%s/target/classes:%s/target/test-classes" % (project_path, project_path)
        lib_path = "%s/lib/" % (project_path)
        for root, dirnames, filenames in os.walk(lib_path):
            for filename in fnmatch.filter(filenames, '*.jar'):
                classpath = classpath + ":" + os.path.join(root, filename)
        
        """ 
        LOG4J and global.properties configuration 
        """
        log4jpath = "-Dlog4j.configurationFile=file:%s" % (project_path + "/cfglog/log4j2.xml")
        logger.debug(log4jpath)
        """
        Start JVM
        """
        jpype.startJVM(jpype.getDefaultJVMPath(), classpath, log4jpath)
        
        # Test JVM
        jpype.java.lang.System.out.println("**[PythonMockDataClay]** Started JVM successfully.")

        # get the Java classes we want to use
        mock_dataclay_class = jpype.JClass("mock.MockDataClay")
        self.mock_dataclay = mock_dataclay_class("test", self.num_storagelocs)
        self.mock_dataclay.startDataClaySimulation()
        
    def finishJavaMockDataClay(self):
        logger.debug('**[PythonMockDataClay]** Finish services...')
        self.mock_dataclay.finishServices()
        # and you have to shutdown the VM at the end
        logger.debug('**[PythonMockDataClay]** Shutdown JVM...')
        self.mock_dataclay = None
        # jpype.shutdownJVM()
        logger.debug('**[PythonMockDataClay]** JVM shut down successfully.')
    
    def startLogListener(self):
        """ start listener logging """ 
        from mock.dataclay_logger import listener_process, listener_configurer
        self.multiprocess_queue = multiprocessing.Queue(-1)
        self.log_listener = multiprocessing.Process(target=listener_process,
                                       args=(self.multiprocess_queue, listener_configurer))
        logger.debug("Created log listener %s" % self.log_listener.name)
        self.log_listener.daemon = True
        self.log_listener.start()
    
    def startSimulation(self, test_name):
        self.test_name = test_name
        """ 
        Kill running pytest processes 
        """ 
        # self.kill_pytest_processes()
        
        self.startLogListener()
        
        """"""""""""""""""""
        
        logger.debug('========================= Starting test %s =========================' % str(test_name))
                
        os.environ["DATACLAYCLIENTCONFIG"] = os.path.dirname(os.path.abspath(__file__)) + "/client.properties"
        self.prepareClientPropertiesFile()
        self.startJavaMockDataClay() 
        self.startPythonExecutionEnvironments()
        
    def startPythonExecutionEnvironments(self, starting_ee_port=6867):

        # WARNING: Child process inherits signal handlers
        # Save a reference to the original signal handler for SIGINT.
        default_handler = signal.getsignal(signal.SIGINT)
        
        # Set signal handling of SIGINT to ignore mode.
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        cur_ee_port = starting_ee_port
        from mock.mock_exec_env import MockExecutionEnvironment
        from mock.dataclay_logger import worker_configurer
        k = 1
        for i in range(1, self.num_storagelocs + 1):
            for j in range(0, self.ees_per_sl):
                sl_id = str(i)
                ee_id = str(j)                
                logger.debug('**[PythonMockDataClay]** Creating exec environment process connecting to LM port %s' % self.cur_lm_port)

                process = MockExecutionEnvironment(sl_id, ee_id,
                                                   self.multiprocess_queue,
                                                   worker_configurer,
                                                   self.cur_lm_port, cur_ee_port)
                cur_ee_port = cur_ee_port + 1
                os.environ["DATASERVICE_HOST"] = "localhost"
                process.start()
                logger.debug("** Running process with pid %s **" % process.pid)
    
                self.exec_envs.append(process)
                
                # Wait 5 seconds to avoid starting Exec.Envs concurrently
                time.sleep(5)
                logger.debug('**[PythonMockDataClay]** Execution Environment %s started!' % process.node_id)
                k = k + 1
        # Since we spawned all the necessary processes already, 
        # restore default signal handling for the parent process. 
        signal.signal(signal.SIGINT, default_handler)
        
    def finishSimulation(self):
        from dataclay import api
        logger.debug('**[PythonMockDataClay]** Finish client if started')
        if api.is_initialized(): 
            api.finish()
        
        self.finishPythonExecutionEnvironments()
        logger.debug('**[PythonMockDataClay]** Finishing JVM...')
        self.finishJavaMockDataClay()
        self.cleanFiles()  
        self.multiprocess_queue.put_nowait(None)
        self.log_listener.join()      
        logger.debug('**[PythonMockDataClay]** Finished')
    
    def finishPythonExecutionEnvironments(self):
        
        logger.debug('**[PythonMockDataClay]** Finish requested. Num exec_envs : %i' % (self.num_execenvs))
        cur_id = 1
        try:
            for exec_env in self.exec_envs:
                logger.debug("** [PythonMockDataClay] Killing process with pid %s **" % exec_env.pid)
                # os.kill(int(exec_env.pid), signal.SIGINT)
                exec_env.terminate()
                exec_env.join()
                logger.debug('**[PythonMockDataClay]** Execution Environment %s finished!' % cur_id)
                cur_id = cur_id + 1
        except:
            traceback.print_exc()
            
        self.exec_envs = []

    def restartDataClay(self):
        from dataclay import api
        logger.debug('**[PythonMockDataClay]** Finish client if started')
        if api.is_initialized(): 
            api.finish()
        
        self.finishPythonExecutionEnvironments()
        self.mock_dataclay.finishServicesWithoutCleaningDBs()
        
        logger.debug('**[PythonMockDataClay]** Wait to restart...')
        
        self.multiprocess_queue.put_nowait(None)
        self.log_listener.join()
        self.startLogListener()
        
        self.prepareClientPropertiesFile()
        self.mock_dataclay.restartDataClaySimulation()

        self.startPythonExecutionEnvironments()
        
    def newAccount(self, account_name, password):
        logger.debug('**[PythonMockDataClay]** Creating new account')
        tool_class = jpype.JClass("dataclay.tool.NewAccount")
        tool_class.main([account_name, password])

    def newDataContract(self, owner_name, owner_pass, dataset_name, benef_name):
        logger.debug('**[PythonMockDataClay]** Creating new datacontract')
        tool_class = jpype.JClass("dataclay.tool.NewDataContract")
        tool_class.main([owner_name, owner_pass, dataset_name, benef_name])
    
    def newNamespace(self, owner_name, owner_pass, namespace_name, language):
        logger.debug('**[PythonMockDataClay]** Registering new namespace')
        tool_class = jpype.JClass("dataclay.tool.NewNamespace")
        tool_class.main([owner_name, owner_pass, namespace_name, language])
        
    def newModelProcess(self, q, owner_name, owner_pass, namespace_name, class_path):
        from dataclay.tool.functions import register_model
        contractid = register_model(owner_name, owner_pass, namespace_name, class_path)
        q.put(contractid)

    def newModel(self, owner_name, owner_pass, namespace_name, class_path):
        logger.debug('**[PythonMockDataClay]** Registering new model')
        q = Queue()
        p = Process(target=self.newModelProcess, args=(q, owner_name, owner_pass, namespace_name, class_path))
        p.start()
        contractid = q.get()  # prints "[42, None, 'hello']"
        p.join()
        logger.debug('**[PythonMockDataClay]** New model registered with contractid %s' % str(contractid))
        return contractid

    def getStubs(self, user_name, user_pass, contract_ids_str, stubs_path):
        logger.debug('**[PythonMockDataClay]** Get stubs')
        from dataclay.tool.functions import get_stubs
        p = Process(target=get_stubs, args=(user_name, user_pass, contract_ids_str, stubs_path))
        p.start()
        p.join()
        logger.debug('**[PythonMockDataClay]** Stubs stored in %s' % stubs_path)
        
    def prepareClientPropertiesFile(self):
        path = os.environ["DATACLAYCLIENTCONFIG"]
        open(path, "w").close()  # Empty it
        clientPropsFile = open(path, "w")
        clientPropsFile.write("HOST=localhost\n")
        port = str(self.cur_lm_port)
        clientPropsFile.write("TCPPORT=%s\n" % port)
        clientPropsFile.close()
        
    def prepareSessionFiles(self, user_name, user_pass, stubs_path, datasets, ds_for_store, dataclay_client_config, local_backend):
        logger.debug('**[PythonMockDataClay]** Preparing sesion files')
        
        open("./cfgfiles/session.properties", "w").close()  # Empty it
        sessionFile = open("./cfgfiles/session.properties", "w")
        sessionFile.write("Account=%s\n" % user_name)
        sessionFile.write("Password=%s\n" % user_pass)
        sessionFile.write("StubsClasspath=%s\n" % stubs_path)
        sessionFile.write("DataSets=%s\n" % datasets)
        sessionFile.write("DataSetForStore=%s\n" % ds_for_store)
        sessionFile.write("DataClayClientConfig=%s\n" % dataclay_client_config)
        sessionFile.write("LocalBackend=%s\n" % local_backend)
        sessionFile.close()
        logger.debug('**[PythonMockDataClay]** Session files ready')
        
    def cleanFiles(self):
        try:
            print('**[PythonMockDataClay]** Cleaning configuration files')
            path = os.environ["DATACLAYCLIENTCONFIG"]
            if os.path.exists("./cfgfiles/session.properties"):
                os.remove("./cfgfiles/session.properties")
            if os.path.exists(path):
                os.remove(path)
            logger.debug('**[PythonMockDataClay]** Cleaning stub files')
            if os.path.exists("./stubs"):
                shutil.rmtree("./stubs")
            if os.path.exists("./log"):
                shutil.rmtree("./log")
            from dataclay.util import Configuration
            for i in range(self.num_execenvs):
                node_id = str(i + 1)
                ee_info = Configuration.EE_PERSISTENT_INFO_PATH + "infoEEDS" + node_id
                if os.path.exists(ee_info):
                    os.remove(ee_info)
                    print('**[PythonMockDataClay]** Removing %s' % str(ee_info))
                if os.path.exists("/tmp/pythoneeEE" + node_id + "_0"):
                    shutil.rmtree("/tmp/pythoneeEE" + node_id + "_0")
                    print("**[PythonMockDataClay]** Removing /tmp/pythoneeEE" + node_id + "_0")
        except Exception:
            traceback.print_exc()
            
    def runScriptUsingPyCOMPSs(self, main_file_path):
        
        """ 
        Check PyCOMPSs is installed. 
        """ 
        
        compss_cmd = "runcompss --debug --lang=python --task_execution=storage %s" % (main_file_path)
        
        try:
            logger.debug("**[PythonMockDataClay]** Running PyCOMPSs command %s" % (compss_cmd))
            self.run_command(compss_cmd, os.getcwd())
        except OSError as e:
            if e.errno == os.errno.ENOENT:
                    # handle file not found error.
                assert False, "**[PythonMockDataClay]** ERROR: runcompss command not found. Please make sure COMPSs is installed."
            else:
                    raise
        except Exception as e:
            logger.debug(str(e))
        
        """
        $COMPSS_INSTALL/$RUNCOMPSS_SCRIPT \
        --project=$XML_PATH/project.xml \
        --resources=$XML_PATH/resources.xml \
        --debug \
        --lang=python \
        --task_execution=storage \
        ./main.py
        """

