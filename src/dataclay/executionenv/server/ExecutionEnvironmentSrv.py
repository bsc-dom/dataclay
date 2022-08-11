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

from dataclay_mds.metadata_service import MetadataService
from dataclay_common.exceptions.exceptions import *

from dataclay.commonruntime.Settings import settings
from dataclay.communication.grpc.clients.StorageLocationGrpcClient import SLClient
from dataclay.communication.grpc.clients.LogicModuleGrpcClient import LMClient
from dataclay_common.protos.common_messages_pb2 import LANG_PYTHON
from dataclay.communication.grpc.server.ExecutionEnvironmentService import DataServiceEE
from dataclay.util.classloaders import (
    ClassLoader,
)  # Import after DataClayRuntime to avoid circular imports
from dataclay.util.config.CfgExecEnv import set_defaults
from dataclay.executionenv.ExecutionEnvironment import ExecutionEnvironment
from dataclay.commonruntime.Initializer import logger
from dataclay.util import Configuration


__author__ = "Alex Barcelo <alex.barcelo@bsc.es>"
__copyright__ = "2015 Barcelona Supercomputing Center (BSC-CNS)"

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
        self.execution_environment.runtime.stop_gc()
        logger.info("Flushing all objects to disk")
        self.execution_environment.runtime.flush_all()
        logger.info("Stopping runtime")
        logger.info("Notifying LM, current EE left")
        self.execution_environment.notify_execution_environment_shutdown()

        from dataclay.api import finish

        finish()

    def preface_autoregister(self):
        """Perform a pre-initialization of stuff (prior to the autoregister call)."""
        self.execution_environment.prepareThread()

        # Check if there is an explicit IP for autoregistering
        local_ip = os.getenv("DATASERVICE_HOST", "")
        if not local_ip:
            local_ip = socket.gethostbyname(socket.gethostname())

        # TODO: Remove LogicModule client. Needed for getting stubs.
        lm_client = LMClient(settings.logicmodule_host, settings.logicmodule_port)
        self.execution_environment.runtime.ready_clients["@LM"] = lm_client

        # Starting MetadataService
        # Backends use the MetadataService class instead of calling a gRPC server
        mds = MetadataService(settings.ETCD_HOST, settings.ETCD_PORT)
        self.execution_environment.runtime.ready_clients["@MDS"] = mds

        return local_ip

    def start_autoregister(self, local_ip):
        """Start the autoregister procedure to introduce ourselves to the LogicModule."""
        self.execution_environment.prepareThread()

        logger.info(f"Start Autoregister with {local_ip} local_ip")

        # Setting settings
        execution_environment_id = self.execution_environment.get_execution_environment_id()
        settings.environment_id = execution_environment_id
        sl_name = settings.dataservice_name
        settings.storage_id = sl_name

        max_retries = Configuration.MAX_RETRY_AUTOREGISTER
        sleep_time = Configuration.RETRY_AUTOREGISTER_TIME / 1000

        # Autoregister of ExecutionEnvironment to LogicModule
        # NOTE: Needed to get registered classes from LogicModule
        # TODO: Should be removed when LogicModule is replaced by MetadataService
        lm_client = self.execution_environment.runtime.ready_clients["@LM"]
        retries = 0
        while True:
            try:
                lm_client.autoregister_ee(
                    execution_environment_id,
                    settings.dataservice_name,
                    local_ip,
                    settings.dataservice_port,
                    LANG_PYTHON,
                )
                break
            except Exception as e:
                if retries == max_retries:
                    logger.critical("Could not create channel, aborting")
                    raise
                else:
                    logger.info(
                        f"Could not create channel, retry #{retries} of {max_retries} in {sleep_time} seconds"
                    )
                    time.sleep(sleep_time)
                    retries += 1

        # Autoregister of ExecutionEnvironment to MetadataService
        mds_client = self.execution_environment.runtime.ready_clients["@MDS"]
        mds_client.autoregister_ee(
            execution_environment_id,
            local_ip,
            settings.dataservice_port,
            settings.dataservice_name,
            LANG_PYTHON,
        )

        # Get the StorageLocation info associated to ExecutionEnvironment
        retries = 0
        while True:
            try:
                storage_location = mds_client.get_storage_location(sl_name)
                break
            except StorageLocationDoesNotExistError as e:
                if retries == max_retries:
                    logger.critical(f"Could not get StorageLocation {sl_name}, aborting")
                    raise e
                else:
                    logger.warning(
                        f"StorageLocation {sl_name} not ready, retry #{retries} of {max_retries} in {sleep_time} seconds"
                    )
                    retries += 1
                    time.sleep(sleep_time)

        logger.info(
            f"Starting client to StorageLocation {storage_location.name} at {storage_location.hostname}:{storage_location.port}"
        )

        # Connect to the StorageLocation
        retries = 0
        while True:
            try:
                storage_client = SLClient(storage_location.hostname, storage_location.port)
                break
            except:
                if retries == max_retries:
                    logger.critical(
                        f"Could not connect to storage location at {storage_location.hostname} and {storage_location.port}, aborting"
                    )
                    raise
                else:
                    logger.warning(
                        f"StorageLocation {sl_name} not ready, retry #{retries} of {max_retries} in {sleep_time} seconds",
                    )
                    retries += 1
                    time.sleep(sleep_time)

        logger.info(f"Connected to StorageLocation {sl_name}!")

        # Makes the StorageLocation client globally available
        self.execution_environment.runtime.ready_clients["@STORAGE"] = storage_client
        storage_client.associate_execution_environment(execution_environment_id)

    def start(self):
        """Start the dataClay server (Execution Environment).

        Keep in mind that the configuration in both dataClay's global ConfigOptions
        and the server-specific one called ServerConfigOptions should be accurate.
        Furthermore, this function expects that the caller will take care of the
        dataClay library initialization.

        This function does not return (by itself), so feel free to spawn it inside
        a greenlet or a subprocess (typical in testing)
        """

        # TODO: Restructure settings
        set_defaults()

        # Create the deployment folder and add it to the path
        try:
            os.makedirs(settings.deploy_path_source)
        except OSError as e:
            if e.errno != 17:
                # Not the "File exists" expected error, reraise it
                raise
        sys.path.insert(1, settings.deploy_path_source)

        self.execution_environment = ExecutionEnvironment(
            settings.dataservice_name, settings.server_listen_port
        )

        # 0 or undefined should become None, which becomes a default of 5x number of cores (see futures' docs)
        max_workers = Configuration.THREAD_POOL_WORKERS or None

        self.server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=max_workers),
            options=(
                (
                    "grpc.max_send_message_length",
                    -1,
                ),
                (
                    "grpc.max_receive_message_length",
                    -1,
                ),
            ),
        )
        ee = DataServiceEE(self.execution_environment)

        from dataclay_common.protos import dataservice_pb2_grpc as ds

        ds.add_DataServiceServicer_to_server(ee, self.server)

        address = str(settings.server_listen_addr) + ":" + str(settings.server_listen_port)

        logger.info("Starting DataServiceEE on %s", address)
        try:
            # TODO: Better way for start server?
            self.server.add_insecure_port(address)
            self.server.start()
            # TODO: Check that the server is correctly started
            # TODO:   -> aka "if the port was in use, fail tremendously and loudly

            self.local_ip = self.preface_autoregister()
            self.start_autoregister(self.local_ip)
            ee.ass_client()
            self.running = True
            signal.signal(signal.SIGINT, self.exit_gracefully_signal)
            signal.signal(signal.SIGTERM, self.exit_gracefully_signal)
            logger.info("Started Python Execution environment on %s", address)

            # writes state file
            try:
                f = open("state.txt", "w")
                f.write("READY")
                f.close()
            except:
                logger.info("State file not writable. Skipping file creation.")

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
        sys.stderr.write("** Exiting gracefully **\n")
        self.persist_and_exit()
        self.server.stop(0)
        self.running = False
        sys.stderr.write("EXECUTION ENVIRONMENT GRACEFULLY STOPPED\n")

    def get_name(self):
        return settings.dataservice_name
