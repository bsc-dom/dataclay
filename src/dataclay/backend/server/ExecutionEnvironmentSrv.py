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
import logging
import os
import signal
import socket
import sys
import threading
import time
import traceback
from concurrent import futures

import grpc
from dataclay_common.exceptions.exceptions import *
from dataclay_common.protos.common_messages_pb2 import LANG_PYTHON

from dataclay.runtime.Initializer import logger
from dataclay.runtime import settings
from dataclay.communication.grpc.clients.LogicModuleGrpcClient import LMClient
from dataclay.communication.grpc.clients.StorageLocationGrpcClient import SLClient
from dataclay.communication.grpc.server.execution_environment_servicer import BackendServicer
from dataclay.backend.backend_api import ExecutionEnvironment
from dataclay.util import Configuration
from dataclay.util.classloaders import (
    ClassLoader,
)  # Import after DataClayRuntime to avoid circular imports
from dataclay.util.config.CfgExecEnv import set_defaults

__author__ = "Alex Barcelo <alex.barcelo@bsc.es>"
__copyright__ = "2015 Barcelona Supercomputing Center (BSC-CNS)"

SERVER_TIME_CHECK_SECONDS = 1


class ExecutionEnvironmentSrv(object):
    def __init__(self):
        self.execution_environment = None

    def persist_and_exit(self):
        logger.info("Performing exit hook --persisting files")

        self.execution_environment.runtime.stop_gc()
        logger.info("Flushing all objects to disk")
        self.execution_environment.runtime.flush_all()
        logger.info("Stopping runtime")
        logger.info("Notifying LM, current EE left")
        self.execution_environment.notify_execution_environment_shutdown()

        from dataclay.api import finish

        finish()

    def start_autoregister(self, local_ip):
        """Start the autoregister procedure to introduce ourselves to the LogicModule."""

        logger.info(f"Start Autoregister with {local_ip} local_ip")

        # Setting settings
        execution_environment_id = self.execution_environment.execution_environment_id
        settings.environment_id = execution_environment_id

        # Autoregister of ExecutionEnvironment to MetadataService
        metadata_service = self.execution_environment.runtime.metadata_service
        metadata_service.autoregister_ee(
            execution_environment_id,
            local_ip,
            settings.dataservice_port,
            settings.dataservice_name,
            LANG_PYTHON,
        )

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
            settings.dataservice_name,
            settings.server_listen_port,
            settings.ETCD_HOST,
            settings.ETCD_PORT,
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
        ee = BackendServicer(self.execution_environment)

        from dataclay_common.protos import dataservice_pb2_grpc

        dataservice_pb2_grpc.add_DataServiceServicer_to_server(ee, self.server)

        address = str(settings.server_listen_addr) + ":" + str(settings.server_listen_port)

        logger.info("Starting BackendServicer on %s", address)
        try:
            # TODO: Better way for start server?
            self.server.add_insecure_port(address)
            self.server.start()
            # TODO: Check that the server is correctly started
            # TODO:   -> aka "if the port was in use, fail tremendously and loudly

            self.local_ip = os.getenv("DATASERVICE_HOST", "")
            if not self.local_ip:
                self.local_ip = socket.gethostbyname(socket.gethostname())
            self.start_autoregister(self.local_ip)
            # ee.ass_client()

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
