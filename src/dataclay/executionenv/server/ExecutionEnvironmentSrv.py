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

from dataclay_common.clients.metadata_service_client import MDSClient
from dataclay_mds.metadata_service import MetadataService

from dataclay.commonruntime.Runtime import clean_runtime
from dataclay.commonruntime.Settings import settings
from dataclay.communication.grpc.clients.StorageLocationGrpcClient import SLClient
from dataclay.communication.grpc.clients.LogicModuleGrpcClient import LMClient
from dataclay.communication.grpc.messages.common.common_messages_pb2 import LANG_PYTHON
from dataclay.communication.grpc.server.ExecutionEnvironmentService import DataServiceEE
from dataclay.util.classloaders import (
    ClassLoader,
)  # Import after DataClayRuntime to avoid circular imports
from dataclay.util.config.CfgExecEnv import set_defaults
from dataclay.executionenv.ExecutionEnvironment import ExecutionEnvironment
from dataclay.commonruntime.Initializer import logger
from dataclay.util import Configuration
from dataclay.util.ETCDClientManager import etcdClientMgr


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
        self.execution_environment.get_runtime().stop_gc()
        logger.info("Flushing all objects to disk")
        self.execution_environment.get_runtime().flush_all()
        logger.info("Stopping runtime")
        logger.info("Notifying LM, current EE left")
        self.execution_environment.notify_execution_environment_shutdown()

        from dataclay.api import finish

        finish()
        clean_runtime()

    def preface_autoregister(self):
        """Perform a pre-initialization of stuff (prior to the autoregister call)."""
        self.execution_environment.prepareThread()

        # Check if there is an explicit IP for autoregistering
        local_ip = os.getenv("DATASERVICE_HOST", "")
        if not local_ip:
            local_ip = socket.gethostbyname(socket.gethostname())

        # Starting LogicModule client and saving it to ready_clients to be gloabally available
        logger.info(
            "Starting client to LogicModule at %s:%d",
            settings.logicmodule_host,
            settings.logicmodule_port,
        )
        lm_client = LMClient(settings.logicmodule_host, settings.logicmodule_port)
        self.execution_environment.get_runtime().ready_clients["@LM"] = lm_client

        # Starting MetadataService
        # Backends use the MetadataService class instead of calling a gRPC server
        mds = MetadataService(settings.ETCD_HOST, settings.ETCD_PORT)
        self.execution_environment.get_runtime().ready_clients["@MDS"] = mds

        # logger.info("local_ip %s returned", local_ip)
        return local_ip

    def start_autoregister(self, local_ip):
        """Start the autoregister procedure to introduce ourselves to the LogicModule."""
        self.execution_environment.prepareThread()

        logger.info("Start Autoregister with %s local_ip", local_ip)
        lm_client = self.execution_environment.get_runtime().ready_clients["@LM"]

        sl_found = False
        retries = 0
        max_retries = Configuration.MAX_RETRY_AUTOREGISTER
        sleep_time = Configuration.RETRY_AUTOREGISTER_TIME / 1000
        sl_name = settings.dataservice_name
        while not sl_found:
            try:
                storage_location_id = lm_client.get_storage_location_id(sl_name)
            except:
                if retries > max_retries:
                    logger.warn(f"Could not get storage location named {sl_name}, aborting")
                    raise
                else:
                    logger.info(
                        f"Storage location (usually dsjava) {sl_name} not ready, retry #%d of %i in %i seconds",
                        retries,
                        max_retries,
                        sleep_time,
                    )
                    time.sleep(sleep_time)
                    retries += 1
            else:
                sl_found = True

        logger.info(f"Storage location (usually dsjava) {sl_name} found!")
        logger.info("Registering current execution environment")
        success = False
        retries = 0
        execution_environment_id = self.execution_environment.get_execution_environment_id()
        while not success:
            try:
                # TODO: Remove lm_client.autoregister_ee and use the mds_client
                # We already have storage_location_id from get_storage_location_id (above)
                storage_location_id = lm_client.autoregister_ee(
                    execution_environment_id,
                    settings.dataservice_name,
                    local_ip,
                    settings.dataservice_port,
                    LANG_PYTHON,
                )
            except Exception as e:
                logger.debug("Catched exception of type %s. Message:\n%s", type(e), e)
                if retries > max_retries:
                    logger.warn("Could not create channel, aborting (reraising exception)")
                    raise
                else:
                    logger.info(
                        "Could not create channel, retry #%d of %i in %i seconds",
                        retries,
                        max_retries,
                        sleep_time,
                    )
                    # TODO: Not Very performing, find a better way
                    time.sleep(sleep_time)
                    retries += 1
            else:
                success = True

        logger.info(
            "Current DataService autoregistered. Associated StorageLocationID: %s",
            storage_location_id,
        )
        settings.storage_id = storage_location_id
        settings.environment_id = execution_environment_id

        # Retrieve the storage_location connection data
        # TODO: Get info directly from etcd using dataclay_common.managers.dataclay
        storage_location = lm_client.get_storage_location_info(
            storage_location_id, from_backend=True
        )

        logger.debug(
            "StorageLocation data: {name: '%s', hostname: '%s', port: %d}",
            storage_location.name,
            storage_location.hostname,
            storage_location.port,
        )

        logger.info(
            "Starting client to StorageLocation {%s} at %s:%d",
            storage_location_id,
            storage_location.hostname,
            storage_location.port,
        )
        sl_connected = False
        retries = 0
        while not sl_connected:
            try:
                storage_client = SLClient(storage_location.hostname, storage_location.port)
            except:
                if retries > max_retries:
                    logger.warn(
                        f"Could not connect to storage location at {storage_location.hostname} and {storage_location.port}, aborting"
                    )
                    raise
                else:
                    logger.info(
                        f"Storage location (usually dsjava) {sl_name} not ready, retry #%d of %i in %i seconds",
                        retries,
                        max_retries,
                        sleep_time,
                    )
                    time.sleep(sleep_time)
                    retries += 1
            else:
                sl_connected = True

        logger.info(f"Connected to StorageLocation {sl_name}!")

        # Leave the ready client to the Storage Location globally available
        self.execution_environment.get_runtime().ready_clients["@STORAGE"] = storage_client
        storage_client.associate_execution_environment(execution_environment_id)

        settings.logicmodule_dc_instance_id = lm_client.get_dataclay_id()
        logger.verbose(
            "DataclayInstanceID is %s, storing client in cache", settings.logicmodule_dc_instance_id
        )

        self.execution_environment.get_runtime().ready_clients[
            settings.logicmodule_dc_instance_id
        ] = self.execution_environment.get_runtime().ready_clients["@LM"]

        # Autoregister execution environment to Metadata Service
        mds_client = self.execution_environment.get_runtime().ready_clients["@MDS"]
        mds_client.autoregister_ee(
            str(execution_environment_id),
            settings.dataservice_name,
            local_ip,
            settings.dataservice_port,
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

        # ETCD
        etcdClientMgr.initialize()

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
