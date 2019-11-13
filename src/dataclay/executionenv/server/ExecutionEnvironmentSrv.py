
""" Class description goes here. """

"""The basic dataClay server features for Python Execution Environments.

This module provides the Execution Environment for Python. A basic dataClay
infrastructure is required, mainly:

  - Logic Module
  - Storage Locations
  - [optional] More Execution Environments

Note that this server must be aware of the "local" Storage Location and the
central Logic Module node.
"""
from concurrent import futures
import grpc
import logging
import os
import socket
import sys
import time
import signal
import threading 
import traceback

from dataclay.commonruntime.Runtime import clean_runtime
from dataclay.commonruntime.Settings import settings
from dataclay.communication.grpc.clients.ExecutionEnvGrpcClient import EEClient
from dataclay.communication.grpc.clients.LogicModuleGrpcClient import LMClient
from dataclay.communication.grpc.messages.common.common_messages_pb2 import LANG_PYTHON
from dataclay.communication.grpc.server.ExecutionEnvironmentService import DataServiceEE
from dataclay.util.classloaders import ClassLoader  # Import after DataClayRuntime to avoid circular imports
from dataclay.util.config.CfgExecEnv import set_defaults
from dataclay.executionenv.ExecutionEnvironment import ExecutionEnvironment
from dataclay.commonruntime.Initializer import logger
from dataclay.util import Configuration

__author__ = 'Alex Barcelo <alex.barcelo@bsc.es>'
__copyright__ = '2015 Barcelona Supercomputing Center (BSC-CNS)'

SERVER_TIME_CHECK_SECONDS = 1


class ExecutionEnvironmentSrv(object):
    
    def __init__(self):
        self.execution_environment = None

    def reset_caches(self):
        logger.info("Received SIGHUP --proceeding to reset caches")
        ClassLoader.cached_metaclass_info.clear()
        ClassLoader.cached_metaclasses.clear()
    
    def persist_and_exit(self):
        logger.info("Performing exit hook --persisting files")
        
        self.execution_environment.prepareThread()
        self.execution_environment.get_runtime().stop_gc()
        logger.info("Flushing all objects to disk")
        self.execution_environment.get_runtime().flush_all()
        logger.info("Stopping runtime")
        self.execution_environment.store_ee_info()
        from dataclay.api import finish
        finish()
        clean_runtime()

    def preface_autoregister(self):
        """Perform a pre-initialization of stuff (prior to the autoregister call)."""
        self.execution_environment.prepareThread()
        # logger.info("Preface Autoregister")
    
        # Check if there is an explicit IP for autoregistering
        local_ip = os.getenv("DATASERVICE_HOST", "")
        if not local_ip:
            local_ip = socket.gethostbyname(socket.gethostname())
    
        logger.info("Starting client to LogicModule at %s:%d",
                     settings.logicmodule_host, settings.logicmodule_port)
    
        lm_client = LMClient(settings.logicmodule_host, settings.logicmodule_port)
    
        # Leave the ready client to the LogicModule globally available
        self.execution_environment.get_runtime().ready_clients["@LM"] = lm_client
    
        # logger.info("local_ip %s returned", local_ip)
        return local_ip
    
    def start_autoregister(self, local_ip):
        """Start the autoregister procedure to introduce ourselves to the LogicModule."""
        self.execution_environment.prepareThread()

        logger.info("Start Autoregister with %s local_ip", local_ip)
        lm_client = self.execution_environment.get_runtime().ready_clients["@LM"]
    
        success = False
        retries = 0
        max_retries = Configuration.MAX_RETRY_AUTOREGISTER
        sleep_time = Configuration.RETRY_AUTOREGISTER_TIME / 1000
        execution_environment_id = self.execution_environment.get_execution_environment_id()
        while not success:
            try:
                storage_location_id = lm_client.autoregister_ee(execution_environment_id,
                    settings.dataservice_name,
                    local_ip,
                    settings.dataservice_port,
                    LANG_PYTHON)
            except Exception as e:
                logger.debug("Catched exception of type %s. Message:\n%s", type(e), e)
                if retries > max_retries:
                    logger.warn("Could not create channel, aborting (reraising exception)")
                    raise
                else:
                    logger.info("Could not create channel, retry #%d of %i in %i seconds", retries, max_retries, sleep_time)
                    # TODO: Not Very performing, find a better way
                    time.sleep(sleep_time)
                    retries += 1
            else:
                success = True
    
        logger.info("Current DataService autoregistered. Associated StorageLocationID: %s",
                    storage_location_id)
        settings.storage_id = storage_location_id
        settings.environment_id = execution_environment_id
    
        # Retrieve the storage_location connection data
        storage_location = lm_client.get_storage_location_for_ds(storage_location_id)
    
        logger.debug("StorageLocation data: {name: '%s', hostname: '%s', port: %d}",
                     storage_location.name,
                     storage_location.hostname,
                     storage_location.storageTCPPort)
    
        logger.info("Starting client to StorageLocation {%s} at %s:%d",
                    storage_location_id, storage_location.hostname, storage_location.storageTCPPort)
    
        storage_client = EEClient(storage_location.hostname, storage_location.storageTCPPort)
    
        # Leave the ready client to the Storage Location globally available
        self.execution_environment.get_runtime().ready_clients["@STORAGE"] = storage_client
        storage_client.associate_execution_environment(execution_environment_id)
        
        settings.logicmodule_dc_instance_id = lm_client.get_dataclay_id()
        logger.verbose("DataclayInstanceID is %s, storing client in cache", settings.logicmodule_dc_instance_id)

        self.execution_environment.get_runtime().ready_clients[settings.logicmodule_dc_instance_id] = self.execution_environment.get_runtime().ready_clients["@LM"]

    def start(self):
        """Start the dataClay server (Execution Environment).
    
        Keep in mind that the configuration in both dataClay's global ConfigOptions
        and the server-specific one called ServerConfigOptions should be accurate.
        Furthermore, this function expects that the caller will take care of the
        dataClay library initialization.
    
        This function does not return (by itself), so feel free to spawn it inside
        a greenlet or a subprocess (typical in testing)
        """
        
        set_defaults()

        # Create the deployment folder and add it to the path
        try:
            os.makedirs(settings.deploy_path_source)
        except OSError as e:
            if e.errno != 17:
                # Not the "File exists" expected error, reraise it
                raise
        sys.path.insert(1, settings.deploy_path_source)
        
        self.execution_environment = ExecutionEnvironment(settings.dataservice_name)

        # 0 or undefined should become None, which becomes a default of 5x number of cores (see futures' docs)
        max_workers = Configuration.THREAD_POOL_WORKERS or None

        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers),
                                  options=(('grpc.max_send_message_length', -1,),
                                           ('grpc.max_receive_message_length', -1,),
                                           ))
        ee = DataServiceEE(self.execution_environment)
    
        from dataclay.communication.grpc.generated.dataservice import dataservice_pb2_grpc as ds

        ds.add_DataServiceServicer_to_server(ee, self.server)
    
        address = str(settings.server_listen_addr) + ":" + str(settings.server_listen_port)
    
        logger.info("Starting DataServiceEE on %s", address)
        try:
            # ToDo: Better way for start server?
            self.server.add_insecure_port(address)
            self.server.start()
            # ToDo: Check that the server is correctly started
            # ToDo:   -> aka "if the port was in use, fail tremendously and loudly
    
            self.local_ip = self.preface_autoregister()
            self.start_autoregister(self.local_ip)
            ee.ass_client()
            self.running = True 
            signal.signal(signal.SIGINT, self.exit_gracefully_signal)
            signal.signal(signal.SIGTERM, self.exit_gracefully_signal)
            logger.info("Started Python Execution environment on %s", address)
            
            # write state file 
            f = open("state.txt", "w")
            f.write("READY")
            f.close()
            
            try:
                while self.running:
                    time.sleep(SERVER_TIME_CHECK_SECONDS)
            except RuntimeError:
                logger.info("Runtime Error")
        except:
            traceback.print_exc()
        logger.info("** Finished Python Execution Environment on %s", address)

    def exit_gracefully_signal(self, signum, frame):
        self.exit_gracefully()

    def exit_gracefully(self):
        logger.info("** Exiting gracefully **")
        self.persist_and_exit()
        self.server.stop(0)
        self.running = False 
        
    def get_name(self):
        return settings.dataservice_name
