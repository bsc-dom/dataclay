import logging
import atexit

import grpc

from dataclay_mds.grpc.protos.generated import metadata_service_pb2_grpc
from dataclay_mds.grpc.protos.generated import metadata_service_pb2

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

    def new_session(self, username, credential, contracts, data_sets,
                    data_set_for_store, new_session_lang):

        contracts_list = []

        for con_id in contracts:
            contracts_list.append(Utils.get_msg_id(con_id))

        data_set_list = []
        for data_set in data_sets:
            data_set_list.append(Utils.get_msg_id(data_set))

        request = logicmodule_messages_pb2.NewSessionRequest(
            accountID=Utils.get_msg_id(account_id),
            credential=Utils.get_credential(credential),
            contractIDs=contracts_list,
            dataSetIDs=data_set_list,
            storeDataSet=Utils.get_msg_id(data_set_for_store),
            sessionLang=new_session_lang
        )
        lm_function = lambda request: self.lm_stub.newSession.future(request=request, metadata=self.metadata_call)
        response = self._call_logicmodule(request, lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        return dataclay_yaml_load(response.sessionInfo)


    def new_account(self, username, password):
        request = metadata_service_pb2.NewAccountRequest(username=username, password=password)
        return self.stub.NewAccount(request)

    def new_session(self, username, password):
        request = metadata_service_pb2.NewSessionRequest(username=username, password=password)
        return self.stub.NewSession(request)