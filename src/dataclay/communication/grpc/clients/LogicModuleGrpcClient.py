""" Class description goes here. """

"""gRPC LogicModule Client code - LogicModule methods."""

import itertools
import logging
import sys
import traceback
from datetime import datetime

import grpc
import six

if six.PY2:
    import cPickle as pickle
elif six.PY3:
    import _pickle as pickle

from time import sleep

import dataclay_common.protos.common_messages_pb2 as CommonMessages
from dataclay_common.protos import (common_messages_pb2, logicmodule_messages_pb2,
                                    logicmodule_pb2_grpc)
from grpc._cython.cygrpc import ChannelArgKey

from dataclay.commonruntime.Settings import settings
from dataclay.communication.grpc import Utils
from dataclay.exceptions.exceptions import DataClayException
from dataclay.util import Configuration
from dataclay.util.YamlParser import dataclay_yaml_dump, dataclay_yaml_load

__author__ = "Enrico La Sala <enrico.lasala@bsc.es>"
__copyright__ = "2017 Barcelona Supercomputing Center (BSC-CNS)"

logger = logging.getLogger("dataclay.api")

async_req_send = itertools.count()
async_req_rec = itertools.count()


class LMClient(object):
    def __init__(self, hostname, port):
        self.channel = None
        self.lm_stub = None
        self.metadata_call = []
        self.create_stubs(hostname, port)

    def create_stubs(self, hostname, port):
        """Create the stub and the channel at the address passed by the server."""
        address = str(hostname) + ":" + str(port)

        options = [
            (ChannelArgKey.max_send_message_length, -1),
            (ChannelArgKey.max_receive_message_length, -1),
        ]

        if (
            Configuration.SSL_CLIENT_TRUSTED_CERTIFICATES != ""
            or Configuration.SSL_CLIENT_CERTIFICATE != ""
            or Configuration.SSL_CLIENT_KEY != ""
        ):
            # read in certificates
            options.append(("grpc.ssl_target_name_override", Configuration.SSL_TARGET_AUTHORITY))
            if port != 443:
                service_alias = str(port)
                self.metadata_call.append(("service-alias", service_alias))
                address = f"{hostname}:443"
                logger.info(f"SSL configured: changed address {hostname}:{port} to {hostname}:443")
                logger.info("SSL configured: using service-alias " + service_alias)
            else:
                self.metadata_call.append(("service-alias", Configuration.SSL_TARGET_LM_ALIAS))

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
                logger.error("failed-to-read-cert-keys", reason=e)

            # create credentials
            if trusted_certs is not None:
                credentials = grpc.ssl_channel_credentials(
                    root_certificates=trusted_certs,
                    private_key=client_key,
                    certificate_chain=client_cert,
                )
            else:
                credentials = grpc.ssl_channel_credentials(
                    private_key=client_key, certificate_chain=client_cert
                )

            self.channel = grpc.secure_channel(address, credentials, options)

            logger.info(
                "SSL configured: using SSL_CLIENT_TRUSTED_CERTIFICATES located at "
                + Configuration.SSL_CLIENT_TRUSTED_CERTIFICATES
            )
            logger.info(
                "SSL configured: using SSL_CLIENT_CERTIFICATE located at "
                + Configuration.SSL_CLIENT_CERTIFICATE
            )
            logger.info(
                "SSL configured: using SSL_CLIENT_KEY located at " + Configuration.SSL_CLIENT_KEY
            )
            logger.info("SSL configured: using authority  " + Configuration.SSL_TARGET_AUTHORITY)

        else:
            self.channel = grpc.insecure_channel(address, options)
            logger.info("SSL not configured")

        try:
            logger.info("Connecting to address %s" % address)
            grpc.channel_ready_future(self.channel).result(
                timeout=Configuration.GRPC_CHECK_ALIVE_TIMEOUT
            )
        except Exception as e:
            logger.debug("Error connecting to server %s. Retrying" % address)
            raise e

        logger.debug("Connected to server %s! " % address)

        self.lm_stub = logicmodule_pb2_grpc.LogicModuleStub(self.channel)

    def close(self):
        """Closing channel by deleting channel and stub"""
        del self.channel
        del self.lm_stub
        self.channel = None
        self.lm_stub = None

    def _call_logicmodule(self, request, lm_function):
        try:
            response = None
            future = lm_function(request)
            i = 0
            while i < Configuration.MAX_RETRIES_LOGICMODULE:
                try:
                    response = future.result()
                    break
                except Exception as e:
                    i = i + 1
                    if i > Configuration.MAX_RETRIES_LOGICMODULE:
                        logger.warning("Max retries reached", exc_info=True)
                        raise e
                    else:
                        logger.debug("Received exception, will retry", exc_info=True)
                        logger.info(
                            "Sleeping for %i seconds " % Configuration.SLEEP_RETRIES_LOGICMODULE
                        )
                        sleep(Configuration.SLEEP_RETRIES_LOGICMODULE)
        except:
            traceback.print_exc()
            raise

        return response

    def autoregister_ee(self, id, name, hostname, port, lang):

        request = logicmodule_messages_pb2.AutoRegisterEERequest(
            executionEnvironmentID=Utils.get_msg_id(id),
            eeName=name,
            eeHostname=hostname,
            eePort=port,
            lang=lang,
        )
        lm_function = lambda request: self.lm_stub.autoregisterEE.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.excInfo.isException:
            logger.debug("Exception in response")
            raise DataClayException(response.excInfo.exceptionMessage)

        st_loc_id = Utils.get_id(response.storageLocationID)
        return st_loc_id

    def get_storage_location_id(self, sl_name):
        request = logicmodule_messages_pb2.GetStorageLocationIDRequest(
            slName=sl_name,
        )
        lm_function = lambda request: self.lm_stub.getStorageLocationID.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)
        st_loc_id = Utils.get_id(response.storageLocationID)
        return st_loc_id

    def perform_set_of_new_accounts(self, admin_id, admin_credential, yaml_file):

        request = logicmodule_messages_pb2.PerformSetAccountsRequest(
            accountID=Utils.get_msg_id(admin_id),
            credential=Utils.get_credential(admin_credential),
            yaml=yaml_file,
        )
        lm_function = lambda request: self.lm_stub.performSetOfNewAccounts.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        result = Utils.prepare_bytes(response.resultYaml)
        return result

    def perform_set_of_operations(self, performer_id, performer_credential, yaml_file):

        request = logicmodule_messages_pb2.PerformSetOperationsRequest(
            accountID=Utils.get_msg_id(performer_id),
            credential=Utils.get_credential(performer_credential),
            yaml=yaml_file,
        )
        lm_function = lambda request: self.lm_stub.performSetOfOperations.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        result = Utils.prepare_bytes(response.resultYaml)

        return result

    def publish_address(self, hostname, port):
        request = logicmodule_messages_pb2.PublishAddressRequest(
            hostname=hostname,
            port=port,
        )
        lm_function = lambda request: self.lm_stub.publishAddress.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

    # Methods for Account Manager

    def new_account(self, admin_account_id, admin_credential, account):

        acc_yaml = dataclay_yaml_dump(account)

        request = logicmodule_messages_pb2.NewAccountRequest(
            adminID=Utils.get_msg_id(admin_account_id),
            admincredential=Utils.get_credential(admin_credential),
            yamlNewAccount=acc_yaml,
        )
        lm_function = lambda request: self.lm_stub.newAccount.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        return Utils.get_id(response.newAccountID)

    def get_account_id(self, account_name):

        request = logicmodule_messages_pb2.GetAccountIDRequest(accountName=account_name)
        lm_function = lambda request: self.lm_stub.getAccountID.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        return Utils.get_id(response.newAccountID)

    def get_account_list(self, admin_account_id, admin_credential):

        request = logicmodule_messages_pb2.GetAccountListRequest(
            adminID=Utils.get_msg_id(admin_account_id),
            admincredential=Utils.get_credential(admin_credential),
        )
        lm_function = lambda request: self.lm_stub.getAccountList.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        result = set()

        for acc_id in response.accountIDs:
            result.add(Utils.get_id(acc_id))

        return result

    # Methods for Session Manager

    def new_session(
        self, account_id, credential, contracts, data_sets, data_set_for_store, new_session_lang
    ):

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
            sessionLang=new_session_lang,
        )
        lm_function = lambda request: self.lm_stub.newSession.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        return dataclay_yaml_load(response.sessionInfo)

    def get_info_of_session_for_ds(self, session_id):

        request = logicmodule_messages_pb2.GetInfoOfSessionForDSRequest(
            sessionID=Utils.get_msg_id(session_id)
        )
        lm_function = lambda request: self.lm_stub.getInfoOfSessionForDS.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        ds_id = Utils.get_id(response.dataSetID)

        calendar = datetime.fromtimestamp(response.date / 1e3).strftime("%Y-%m-%d %H:%M:%S")

        data_sets = set()

        for datas_id in response.dataSetIDs:
            data_sets.add(Utils.get_id(datas_id))

        t = (ds_id, data_sets), calendar
        return t

    # Methods for Namespace Manager

    def new_namespace(self, account_id, credential, namespace):

        yaml_dom = dataclay_yaml_dump(namespace)

        request = logicmodule_messages_pb2.NewNamespaceRequest(
            accountID=account_id,
            credential=Utils.get_credential(credential),
            newNamespaceYaml=yaml_dom,
        )
        lm_function = lambda request: self.lm_stub.newNamespace.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        return Utils.get_id(response.namespaceID)

    def remove_namespace(self, account_id, credential, namespace_name):

        request = logicmodule_messages_pb2.RemoveNamespaceRequest(
            accountID=Utils.get_msg_id(account_id),
            credential=Utils.get_credential(credential),
            namespaceName=namespace_name,
        )
        lm_function = lambda request: self.lm_stub.removeNamespace.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def get_namespace_id(self, account_id, credential, namespace_name):

        request = logicmodule_messages_pb2.GetNamespaceIDRequest(
            accountID=Utils.get_msg_id(account_id),
            credential=Utils.get_credential(credential),
            namespaceName=namespace_name,
        )
        lm_function = lambda request: self.lm_stub.getNamespaceID.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        return Utils.get_id(response.namespaceID)

    def get_object_dataset_id(self, session_id, oid):

        request = logicmodule_messages_pb2.GetObjectDataSetIDRequest(
            sessionID=Utils.get_msg_id(session_id), objectID=Utils.get_msg_id(oid)
        )
        lm_function = lambda request: self.lm_stub.getObjectDataSetID.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        return Utils.get_id(response.dataSetID)

    def get_classname_and_namespace_for_ds(self, class_id):

        request = logicmodule_messages_pb2.GetClassNameAndNamespaceForDSRequest(
            classID=Utils.get_msg_id(class_id)
        )
        lm_function = lambda request: self.lm_stub.getClassNameAndNamespaceForDS.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        return response.className, response.namespace

    def get_dataset_id(self, account_id, credential, dataset_name):

        request = logicmodule_messages_pb2.GetDataSetIDRequest(
            accountID=Utils.get_msg_id(account_id),
            credential=Utils.get_credential(credential),
            dataSetName=dataset_name,
        )
        lm_function = lambda request: self.lm_stub.getDataSetID.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        return Utils.get_id(response.dataSetID)

    # Methods for Class Manager

    def new_class(self, account_id, credential, language, new_classes):

        new_cl = {}

        for klass in new_classes:
            yaml_str = dataclay_yaml_dump(klass)
            new_cl[klass.name] = yaml_str

        request = logicmodule_messages_pb2.NewClassRequest(
            accountID=Utils.get_msg_id(account_id),
            credential=Utils.get_credential(credential),
            language=language,
            newClasses=new_cl,
        )
        lm_function = lambda request: self.lm_stub.newClass.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        result = dict()

        for k, v in response.newClasses.items():
            result[k] = dataclay_yaml_load(v)

        return result

    def remove_class(self, account_id, credential, namespace_id, class_name):

        request = logicmodule_messages_pb2.RemoveClassRequest(
            accountID=Utils.get_msg_id(account_id),
            credential=Utils.get_credential(credential),
            className=class_name,
        )
        lm_function = lambda request: self.lm_stub.removeClass.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.isException:
            raise DataClayException(response.exceptionMessage)

    # Methods for MetaDataService for DS
    def get_storage_location_info(self, st_loc_id, from_backend=False):

        request = logicmodule_messages_pb2.GetStorageLocationInfoRequest(
            storageLocationID=Utils.get_msg_id(st_loc_id), fromBackend=from_backend
        )
        lm_function = lambda request: self.lm_stub.getStorageLocationInfo.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        return Utils.get_storage_location(response.storageLocationInfo)

    def get_executionenvironment_info(self, backend_id, from_backend=False):

        request = logicmodule_messages_pb2.GetExecutionEnvironmentInfoRequest(
            execEnvID=Utils.get_msg_id(backend_id), fromBackend=from_backend
        )
        lm_function = lambda request: self.lm_stub.getExecutionEnvironmentInfo.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        return Utils.get_execution_environment(response.executionEnvironmentInfo)

    def get_external_executionenvironment_info(self, backend_id):

        request = logicmodule_messages_pb2.GetExternalExecutionEnvironmentInfoRequest(
            execEnvID=Utils.get_msg_id(backend_id)
        )
        lm_function = lambda request: self.lm_stub.getExternalExecutionEnvironmentInfo.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        return Utils.get_external_execution_environment(response.executionEnvironmentInfo)

    def get_dataclays_object_is_federated_with(self, object_id):
        request = logicmodule_messages_pb2.GetDataClaysObjectIsFederatedWithRequest(
            objectID=Utils.get_msg_id(object_id)
        )
        lm_function = lambda request: self.lm_stub.getDataClaysObjectIsFederatedWith.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        result = set()
        for curdataClayID in response.extDataClayIDs:
            result.add(Utils.get_id(curdataClayID))

        return result

    def register_objects_from_gc(self, reg_info, backend_id):

        reg_info_set = CommonMessages.RegistrationInfo(
            objectID=Utils.get_msg_id(reg_info.object_id),
            classID=Utils.get_msg_id(reg_info.class_id),
            sessionID=Utils.get_msg_id(reg_info.store_session_id),
            dataSetID=Utils.get_msg_id(reg_info.dataset_name),
            alias=reg_info.alias,
        )

        request = logicmodule_messages_pb2.RegisterObjectForGCRequest(
            regInfo=reg_info_set, backendID=Utils.get_msg_id(backend_id)
        )

        lm_function = lambda request: self.lm_stub.registerObjectFromGC.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)

        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def register_objects(self, reg_infos, backend_id, lang):

        reg_infos_msg = list()
        for reg_info in reg_infos:
            msg_reg_info = CommonMessages.RegistrationInfo(
                objectID=Utils.get_msg_id(reg_info.object_id),
                classID=Utils.get_msg_id(reg_info.class_id),
                sessionID=Utils.get_msg_id(reg_info.store_session_id),
                dataSetID=Utils.get_msg_id(reg_info.dataset_name),
                alias=reg_info.alias,
            )
            reg_infos_msg.append(msg_reg_info)

        request = logicmodule_messages_pb2.RegisterObjectsRequest(
            regInfos=reg_infos_msg, backendID=Utils.get_msg_id(backend_id), lang=lang
        )

        lm_function = lambda request: self.lm_stub.registerObjects.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        result = list()
        for oid in response.objectIDs:
            result.append(Utils.get_id(oid))
        return result

    def set_dataset_id_from_garbage_collector(self, object_id, dataset_name):

        request = logicmodule_messages_pb2.SetDataSetIDFromGarbageCollectorRequest(
            objectID=Utils.get_msg_id(object_id), datasetID=Utils.get_msg_id(dataset_name)
        )

        # ToDo: In Java at this point override the onNext/onError/onCompleted methods of responseObserver

        try:
            logger.trace(
                "Asynchronous call to register object from Garbage Collector for object %s",
                object_id,
            )

            # ToDo: check async
            six.advance_iterator(async_req_send)

            resp_future = self.lm_stub.setDataSetIDFromGarbageCollector.future.future(
                request=request, metadata=self.metadata_call
            )
            resp_future.result()

            if resp_future.done():
                six.advance_iterator(async_req_rec)

        except RuntimeError as e:
            raise e

        if resp_future.isException:
            raise DataClayException(resp_future.exceptionMessage)

    # Methods for MetaDataService
    def get_dataclay_id(self):

        lm_function = lambda request: self.lm_stub.getDataClayID.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(CommonMessages.EmptyMessage(), lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.exceptionMessage)

        return Utils.get_id(response.dataClayID)

    def federate_object(self, session_id, object_id, ext_dataclay_id, recursive):
        request = logicmodule_messages_pb2.FederateObjectRequest(
            sessionID=Utils.get_msg_id(session_id),
            objectID=Utils.get_msg_id(object_id),
            extDataClayID=Utils.get_msg_id(ext_dataclay_id),
            recursive=recursive,
        )
        lm_function = lambda request: self.lm_stub.federateObject.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def unfederate_object(self, session_id, object_id, ext_dataclay_id, recursive):
        request = logicmodule_messages_pb2.UnfederateObjectRequest(
            sessionID=Utils.get_msg_id(session_id),
            objectID=Utils.get_msg_id(object_id),
            extDataClayID=Utils.get_msg_id(ext_dataclay_id),
            recursive=recursive,
        )
        lm_function = lambda request: self.lm_stub.unfederateObject.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def get_external_dataclay_id(self, dcHost, dcPort):
        request = logicmodule_messages_pb2.GetExternalDataclayIDRequest(host=dcHost, port=dcPort)
        lm_function = lambda request: self.lm_stub.getExternalDataclayId.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        return Utils.get_id(response.extDataClayID)

    def get_external_dataclay_info(self, ext_dataclay_id):
        request = logicmodule_messages_pb2.GetExtDataClayInfoRequest(
            extDataClayID=Utils.get_msg_id(ext_dataclay_id)
        )
        lm_function = lambda request: self.lm_stub.getExternalDataClayInfo.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        return Utils.get_dataclay_instance(response.extDataClayInfo)

    def get_all_execution_environments_info(self, language, get_external=True, from_backend=False):

        request = logicmodule_messages_pb2.GetAllExecutionEnvironmentsInfoRequest(
            execEnvLang=language, getExternal=get_external, fromBackend=from_backend
        )
        lm_function = lambda request: self.lm_stub.getAllExecutionEnvironmentsInfo.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        result = dict()

        for k, v in response.execEnvs.items():
            result[Utils.get_id(k)] = Utils.get_execution_environment(v)

        return result

    def get_object_info(self, session_id, object_id):

        request = logicmodule_messages_pb2.GetObjectInfoRequest(
            sessionID=Utils.get_msg_id(session_id), objectID=Utils.get_msg_id(object_id)
        )
        lm_function = lambda request: self.lm_stub.getObjectInfo.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        return response.classname, response.namespace

    def get_object_from_alias(self, session_id, alias):

        request = logicmodule_messages_pb2.GetObjectFromAliasRequest(
            sessionID=Utils.get_msg_id(session_id), alias=alias
        )
        lm_function = lambda request: self.lm_stub.getObjectFromAlias.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        t = (
            Utils.get_id(response.objectID),
            Utils.get_id(response.classID),
            Utils.get_id(response.hint),
        )

        return t

    def delete_alias(self, session_id, alias):

        request = logicmodule_messages_pb2.DeleteAliasRequest(
            sessionID=Utils.get_msg_id(session_id), alias=alias
        )
        lm_function = lambda request: self.lm_stub.deleteAlias.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        return Utils.get_id(response.objectID)

    # Methods for Storage Location

    def set_dataset_name(self, session_id, object_id, dataset_name):

        request = logicmodule_messages_pb2.SetDataSetIDRequest(
            sessionID=Utils.get_msg_id(session_id),
            objectID=Utils.get_msg_id(object_id),
            datasetID=Utils.get_msg_id(dataset_name),
        )
        lm_function = lambda request: self.lm_stub.setDataSetID.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def move_object(self, session_id, object_id, src_backend_id, dest_backend_id, recursive):

        request = logicmodule_messages_pb2.MoveObjectRequest(
            sessionID=Utils.get_msg_id(session_id),
            objectID=Utils.get_msg_id(object_id),
            srcBackendID=Utils.get_msg_id(src_backend_id),
            destBackendID=Utils.get_msg_id(dest_backend_id),
            recursive=recursive,
        )
        lm_function = lambda request: self.lm_stub.moveObject.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        result = list()

        for oid in response.objectIDs:
            result.append(Utils.get_id(oid))

        return result

    def set_object_read_only(self, session_id, object_id):

        request = logicmodule_messages_pb2.SetObjectReadOnlyRequest(
            sessionID=Utils.get_msg_id(session_id), objectID=Utils.get_msg_id(object_id)
        )
        lm_function = lambda request: self.lm_stub.setObjectReadOnly.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def set_object_read_write(self, session_id, object_id):

        request = logicmodule_messages_pb2.SetObjectReadWriteRequest(
            sessionID=Utils.get_msg_id(session_id), objectID=Utils.get_msg_id(object_id)
        )
        lm_function = lambda request: self.lm_stub.setObjectReadWrite.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def register_external_dataclay(self, exthostname, extport):

        request = logicmodule_messages_pb2.RegisterExternalDataClayRequest(
            hostname=exthostname, port=extport
        )
        lm_function = lambda request: self.lm_stub.registerExternalDataClay.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        return Utils.get_id(response.extDataClayID)

    def get_metadata_by_oid(self, session_id, object_id):

        request = logicmodule_messages_pb2.GetMetadataByOIDRequest(
            sessionID=Utils.get_msg_id(session_id), objectID=Utils.get_msg_id(object_id)
        )
        lm_function = lambda request: self.lm_stub.getMetadataByOID.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        logger.debug("Obtained metadata info %s" % str(response))
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        return Utils.get_metadata_info(response.mdInfo)

    # Methods for Execution Environment

    def execute_implementation(
        self, session_id, operation_id, remote_implementation, object_id, params
    ):

        request = logicmodule_messages_pb2.ExecuteImplementationRequest(
            sessionID=Utils.get_msg_id(session_id),
            operationID=Utils.get_msg_id(operation_id),
            implementationID=Utils.get_msg_id(remote_implementation[0]),
            contractID=Utils.get_msg_id(remote_implementation[1]),
            interfaceID=Utils.get_msg_id(remote_implementation[2]),
            params=Utils.get_param_or_return(params),
            objectID=Utils.get_msg_id(object_id),
        )
        lm_function = lambda request: self.lm_stub.executeImplementation.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.excInfo.isException:
            try:
                exception = pickle.loads(response.excInfo.serializedException)
            except:
                raise DataClayException(response.excInfo.exceptionMessage)
            else:
                raise exception

        if response.ret is not None:
            return Utils.get_param_or_return(response.ret)
        else:
            return None

    def synchronize_federated_object(self, dataclay_id, object_id, impl_id, params):

        if params is not None:
            request = logicmodule_messages_pb2.SynchronizeFederatedObjectRequest(
                extDataClayID=Utils.get_msg_id(dataclay_id),
                objectID=Utils.get_msg_id(object_id),
                implementationID=Utils.get_msg_id(impl_id),
                params=Utils.get_param_or_return(params),
            )
        else:
            request = logicmodule_messages_pb2.SynchronizeFederatedObjectRequest(
                extDataClayID=Utils.get_msg_id(dataclay_id),
                objectID=Utils.get_msg_id(object_id),
                implementationID=Utils.get_msg_id(impl_id),
            )

        lm_function = lambda request: self.lm_stub.synchronizeFederatedObject.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)

        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def is_prefetching_enabled(self):
        lm_function = lambda request: self.lm_stub.isPrefetchingEnabled.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(CommonMessages.EmptyMessage(), lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)
        return response.enabled

    def check_alive(self):
        lm_function = lambda request: self.lm_stub.checkAlive.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(CommonMessages.EmptyMessage(), lm_function)
        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def object_exists_in_dataclay(self, object_id):
        request = logicmodule_messages_pb2.ObjectExistsInDataClayRequest(
            objectID=Utils.get_msg_id(object_id)
        )
        lm_function = lambda request: self.lm_stub.objectExistsInDataClay.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)

        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)
        return response.exists

    def get_num_objects(self):
        lm_function = lambda request: self.lm_stub.getNumObjects.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(CommonMessages.EmptyMessage(), lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)
        return response.numObjs

    # Methods for Stubs

    def get_stubs(self, applicant_account_id, applicant_credential, language, contracts_ids):

        cid_list = []

        for cID in contracts_ids:
            cid_list.append(Utils.get_msg_id(cID))

        request = logicmodule_messages_pb2.GetStubsRequest(
            applicantAccountID=Utils.get_msg_id(applicant_account_id),
            credentials=Utils.get_credential(applicant_credential),
            language=language,
            contractIDs=cid_list,
        )
        lm_function = lambda request: self.lm_stub.getStubs.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        result = dict()

        for k, v in response.stubs.items():
            result[k] = v

        return result

    def get_babel_stubs(self, applicant_account_id, applicant_credential, contracts_ids):

        cid_list = []

        for cID in contracts_ids:
            cid_list.append(Utils.get_msg_id(cID))

        request = logicmodule_messages_pb2.GetBabelStubsRequest(
            accountID=Utils.get_msg_id(applicant_account_id),
            credentials=Utils.get_credential(applicant_credential),
            contractIDs=cid_list,
        )
        lm_function = lambda request: self.lm_stub.getBabelStubs.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        return response.yamlStub

    # Notification Manager Methods

    def register_event_listener_implementation(self, account_id, credential, new_event_listener):

        request = logicmodule_messages_pb2.RegisterECARequest(
            applicantAccountID=Utils.get_msg_id(account_id),
            credentials=Utils.get_credential(credential),
            eca=dataclay_yaml_dump(new_event_listener),
        )
        lm_function = lambda request: self.lm_stub.registerECA.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

    def advise_event(self, new_event):

        request = logicmodule_messages_pb2.AdviseEventRequest(
            eventYaml=dataclay_yaml_dump(new_event)
        )
        lm_function = lambda request: self.lm_stub.adviseEvent.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.isException:
            raise DataClayException(response.exceptionMessage)

    # Garbage Collector Methods

    def close_session(self, session_id):

        request = logicmodule_messages_pb2.CloseSessionRequest(
            sessionID=Utils.get_msg_id(session_id)
        )
        lm_function = lambda request: self.lm_stub.closeSession.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.isException:
            raise DataClayException(response.exceptionMessage)

    # Paraver Methods

    def activate_tracing(self, task_id):
        request = logicmodule_messages_pb2.ActivateTracingRequest(taskid=task_id)
        lm_function = lambda request: self.lm_stub.activateTracing.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def deactivate_tracing(self):
        lm_function = lambda request: self.lm_stub.deactivateTracing.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(CommonMessages.EmptyMessage(), lm_function)
        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def get_traces(self):
        lm_function = lambda request: self.lm_stub.getTraces.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(CommonMessages.EmptyMessage(), lm_function)
        if response.excInfo.isException:
            raise DataClayException(response.excInfo.exceptionMessage)

        result = dict()
        for k, v in response.traces.items():
            result[k] = v

        return result

    def wait_and_process_async_req(self):
        # ToDo: wait all the async requests in a proper way

        while async_req_send != async_req_rec:
            try:
                return
            except NotImplementedError as e:
                raise Exception(e.message)

    def add_alias(self, object_id, alias):

        request = logicmodule_messages_pb2.AddAliasRequest(
            objectIDToHaveAlias=Utils.get_msg_id(object_id), alias=alias
        )
        lm_function = lambda request: self.lm_stub.addAlias.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def import_models_from_external_dataclay(self, namespace, ext_dataclay_id):
        request = logicmodule_messages_pb2.ImportModelsFromExternalDataClayRequest(
            namespaceName=namespace, dataClayID=Utils.get_msg_id(ext_dataclay_id)
        )
        lm_function = lambda request: self.lm_stub.importModelsFromExternalDataClay.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.isException:
            raise DataClayException(response.exceptionMessage)

    def notify_execution_environment_shutdown(self, exec_env_id):
        request = logicmodule_messages_pb2.NotifyExecutionEnvironmentShutdownRequest(
            executionEnvironmentID=Utils.get_msg_id(exec_env_id)
        )
        lm_function = lambda request: self.lm_stub.notifyExecutionEnvironmentShutdown.future(
            request=request, metadata=self.metadata_call
        )
        response = self._call_logicmodule(request, lm_function)
        if response.isException:
            raise DataClayException(response.exceptionMessage)

    ################## EXTRAE IGNORED FUNCTIONS ###########################
    deactivate_tracing.do_not_trace = True
    activate_tracing.do_not_trace = True
