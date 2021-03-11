
""" Class description goes here. """

"""gRPC ExecutionEnvironment Client code - StorageLocation/EE methods."""

import logging
import sys
import traceback
import six
import grpc

if six.PY2:
    import cPickle as pickle
elif six.PY3:
    import _pickle as pickle

from grpc._cython.cygrpc import ChannelArgKey
from dataclay.commonruntime.Settings import settings
from dataclay.communication.grpc import Utils
from dataclay.communication.grpc.generated.dataservice import dataservice_pb2_grpc
from dataclay.communication.grpc.messages.dataservice import dataservice_messages_pb2
from dataclay.exceptions.exceptions import DataClayException
from dataclay.util.YamlParser import dataclay_yaml_dump
import dataclay.communication.grpc.messages.common.common_messages_pb2 as CommonMessages
from dataclay.util import Configuration

__author__ = 'Enrico La Sala <enrico.lasala@bsc.es>'
__copyright__ = '2017 Barcelona Supercomputing Center (BSC-CNS)'

logger = logging.getLogger(__name__)


class SLClient(object):

    def __init__(self, hostname, port):
        """Create the stub and the channel at the address passed by the server."""
        self.address = str(hostname) + ":" + str(port)
        options = [(ChannelArgKey.max_send_message_length, -1),
                   (ChannelArgKey.max_receive_message_length, -1)]
        self.metadata_call = []
        if Configuration.SSL_CLIENT_TRUSTED_CERTIFICATES != "" or \
                Configuration.SSL_CLIENT_CERTIFICATE != "" or \
                Configuration.SSL_CLIENT_KEY != "":
            # read in certificates
            options.append(('grpc.ssl_target_name_override', Configuration.SSL_TARGET_AUTHORITY))
            if port != 443:
                service_alias = str(port)
                self.metadata_call.append(('service-alias', service_alias))
                self.address = f"{hostname}:443"
                logger.info(f"SSL configured: changed address {hostname}:{port} to {hostname}:443")
                logger.info("SSL configured: using service-alias  " + service_alias)
            else:
                self.metadata_call.append(('service-alias', Configuration.SSL_TARGET_SL_ALIAS))

            try:
                if Configuration.SSL_CLIENT_TRUSTED_CERTIFICATES != "":
                    with open(Configuration.SSL_CLIENT_TRUSTED_CERTIFICATES, "rb") as f:
                        trusted_certs = f.read()
                if Configuration.SSL_CLIENT_CERTIFICATE != "":
                    with open(Configuration.SSL_CLIENT_CERTIFICATE, "rb") as f:
                        client_cert = f.read()

                if Configuration.SSL_CLIENT_KEY != "":
                    with open(Configuration.SSL_CLIENT_KEY, "rb") as f:
                        client_key = f.read()
            except Exception as e:
                logger.error('failed-to-read-cert-keys', reason=e)

            # create credentials
            if trusted_certs is not None:
                credentials = grpc.ssl_channel_credentials(root_certificates=trusted_certs,
                                                           private_key=client_key,
                                                           certificate_chain=client_cert)
            else:
                credentials = grpc.ssl_channel_credentials(private_key=client_key,
                                                           certificate_chain=client_cert)

            self.channel = grpc.secure_channel(self.address, credentials, options)

            logger.info("SSL configured: using SSL_CLIENT_TRUSTED_CERTIFICATES located at " + Configuration.SSL_CLIENT_TRUSTED_CERTIFICATES)
            logger.info("SSL configured: using SSL_CLIENT_CERTIFICATE located at " + Configuration.SSL_CLIENT_CERTIFICATE)
            logger.info("SSL configured: using SSL_CLIENT_KEY located at " + Configuration.SSL_CLIENT_KEY)
            logger.info("SSL configured: using authority  " + Configuration.SSL_TARGET_AUTHORITY)

        else:
            self.channel = grpc.insecure_channel(self.address, options)
            logger.info("SSL not configured")

        try:
            grpc.channel_ready_future(self.channel).result(timeout=Configuration.GRPC_CHECK_ALIVE_TIMEOUT)
        except Exception as e:
            sys.exit('Error connecting to server %s' % self.address)
        else:
            self.ds_stub = dataservice_pb2_grpc.DataServiceStub(self.channel)

    def close(self):
        """Closing channel by deleting channel and stub"""
        del self.channel
        del self.ds_stub
        self.channel = None
        self.ds_stub = None
    
    # STORAGE LOCATION - DBHANDLER

    def update_refs(self, ref_counting):
        
        """ ref_counting is a dict uuid - integer """ 
        request = dataservice_messages_pb2.UpdateRefsRequest(
            refsToUpdate=ref_counting
        )

        try:
            response = self.ds_stub.updateRefs(request, metadata=self.metadata_call)
        
        except RuntimeError as e:
            raise e
        
        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def store_to_db(self, execution_environment_id, object_id, obj_bytes):
        
        request = dataservice_messages_pb2.StoreToDBRequest(
            executionEnvironmentID=Utils.get_msg_id(execution_environment_id),
            objectID=Utils.get_msg_id(object_id),
            objBytes=obj_bytes
        )

        try:
            response = self.ds_stub.storeToDB(request, metadata=self.metadata_call)
        
        except RuntimeError as e:
            raise e
        
        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def get_from_db(self, execution_environment_id, object_id):

        request = dataservice_messages_pb2.GetFromDBRequest(
            executionEnvironmentID=Utils.get_msg_id(execution_environment_id),
            objectID=Utils.get_msg_id(object_id),
        )
        try:
            response = self.ds_stub.getFromDB(request, metadata=self.metadata_call)

        except RuntimeError as e:
            raise e

        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        return response.objBytes
    
    def update_to_db(self, execution_environment_id, object_id, new_obj_bytes, dirty):
        request = dataservice_messages_pb2.UpdateToDBRequest(
            executionEnvironmentID=Utils.get_msg_id(execution_environment_id),
            objectID=Utils.get_msg_id(object_id),
            objBytes=new_obj_bytes,
            dirty=dirty
        )

        try:
            response = self.ds_stub.updateToDB(request, metadata=self.metadata_call)
        
        except RuntimeError as e:
            raise e
        
        if response.isException:
            raise DataClayException(response.exceptionMessage)
    
    def delete_to_db(self, execution_environment_id, object_id):
        request = dataservice_messages_pb2.DeleteToDBRequest(
            executionEnvironmentID=Utils.get_msg_id(execution_environment_id),
            objectID=Utils.get_msg_id(object_id),
        )

        try:
            response = self.ds_stub.deleteToDB(request, metadata=self.metadata_call)
        
        except RuntimeError as e:
            raise e
        
        if response.isException:
            raise DataClayException(response.exceptionMessage)
        
    def associate_execution_environment(self, execution_environment_id):
        request = dataservice_messages_pb2.AssociateExecutionEnvironmentRequest(
            executionEnvironmentID=Utils.get_msg_id(execution_environment_id)
        )

        try:
            response = self.ds_stub.associateExecutionEnvironment(request, metadata=self.metadata_call)
        
        except RuntimeError as e:
            raise e
        
        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def activate_tracing(self, task_id):
        request = dataservice_messages_pb2.ActivateTracingRequest(
            taskid=task_id
        )
        
        try:
            response = self.ds_stub.activateTracing(request, metadata=self.metadata_call)
        
        except RuntimeError as e:
            raise e
        
        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def deactivate_tracing(self):
        try:
            response = self.ds_stub.deactivateTracing(CommonMessages.EmptyMessage(), metadata=self.metadata_call)
        
        except RuntimeError as e:
            raise e
        
        if response.isException:
            raise DataClayException(response.exceptionMessage)
        
    def get_traces(self):
        try:
            response = self.ds_stub.getTraces(CommonMessages.EmptyMessage(), metadata=self.metadata_call)
        except RuntimeError as e:
            raise e
        
        result = dict()
        for k, v in response.stubs.items():
            result[k] = v

        return result
        
    ################## EXTRAE IGNORED FUNCTIONS ###########################
    deactivate_tracing.do_not_trace = True
    activate_tracing.do_not_trace = True
