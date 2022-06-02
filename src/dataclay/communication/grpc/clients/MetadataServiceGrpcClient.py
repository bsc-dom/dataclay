import logging
import atexit

import grpc

from dataclay.protos import metadata_service_pb2_grpc
from dataclay.protos import metadata_service_pb2

logger = logging.getLogger(__name__)

# TODO: Use configparse to read connection details from config file
HOSTNAME = 'localhost'
PORT = 16587

class MDSClient:
    def __init__(self, hostname, port):
        self.address = f'{hostname}:{port}'
        self.channel = grpc.insecure_channel(self.address)
        self.stub = metadata_service_pb2_grpc.MetadataServiceStub(self.channel)
        atexit.register(self.close)

    def close(self):
        self.channel.close()

    # Methods for Session Manager

    def new_session(self, username, password, datasets, dataset_for_store):

        request = metadata_service_pb2.NewSessionRequest(
            username=username,
            password=password,
            datasets=datasets,
            dataset_for_store=dataset_for_store
        )

        response = self.stub.NewSession(request)
        return response

    def new_account(self, username, password):
        request = metadata_service_pb2.NewAccountRequest(username=username, password=password)
        return self.stub.NewAccount(request)
