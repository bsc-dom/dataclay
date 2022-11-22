import logging
import uuid
from uuid import UUID

import etcd3
from dataclay_common.exceptions.exceptions import *
from dataclay.metadata.managers.account import Account, AccountManager
from dataclay.metadata.managers.dataclay import (
    Dataclay,
    DataclayManager,
    ExecutionEnvironment,
    StorageLocation,
)
from dataclay.metadata.managers.dataset import Dataset, DatasetManager
from dataclay.metadata.managers.object import ObjectManager, ObjectMetadata
from dataclay.metadata.managers.session import Session, SessionManager

from opentelemetry import trace

FEDERATOR_ACCOUNT_USERNAME = "Federator"
EXTERNAL_OBJECTS_DATASET_NAME = "ExternalObjects"


# Acquire a tracer and logger
tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)


class MetadataAPI:
    def __init__(self, etcd_host, etcd_port):
        # Creates etcd client
        self.etcd_client = etcd3.client(etcd_host, etcd_port)

        # Creates managers for each class
        self.account_mgr = AccountManager(self.etcd_client)
        self.session_mgr = SessionManager(self.etcd_client)
        self.dataset_mgr = DatasetManager(self.etcd_client)
        self.object_mgr = ObjectManager(self.etcd_client)
        self.dataclay_mgr = DataclayManager(self.etcd_client)

        logger.info("Initialized MetadataService")

    ###################
    # Session Manager #
    ###################

    def new_session(self, username: str, password: str, dataset_name: str) -> Session:
        """Registers a new session

        Validates the account credentials, and creates a new session
        associated to the account and the dataset_name.

        Args:
            username : Accounts username
            password : Accounts password
            dataset_name: Name of the dataset to store objects

        Raises:
            Exception('Account is not valid!'): If wrong credentials
        """
        with tracer.start_as_current_span(
            "new_session", attributes={"username": username, "dataset_name": dataset_name}
        ):
            # Validates account credentials
            account = self.account_mgr.get_account(username)
            if not account.verify(password):
                raise AccountInvalidCredentialsError(username)

            # Validates accounts access to dataset_name
            dataset = self.dataset_mgr.get_dataset(dataset_name)
            if not dataset.is_public and dataset_name not in account.datasets:
                raise DatasetIsNotAccessibleError(dataset_name, username)

            # Creates a new session
            # TODO: ¿Remove namespaces from Session and Account?
            session = Session(
                id=uuid.uuid4(),
                username=username,
                dataset_name=dataset_name,
                is_active=True,
            )
            self.session_mgr.put_session(session)

            logger.info(f"Created new session for {username} with id {session.id}")
            return session

    def get_session(self, session_id: UUID) -> Session:
        with tracer.start_as_current_span(
            "get_session", attributes={"session_id": str(session_id)}
        ):
            return self.session_mgr.get_session(session_id)

    def close_session(self, session_id: UUID):
        with tracer.start_as_current_span(
            "close_session", attributes={"session_id": str(session_id)}
        ):
            # TODO: decide if close session remove the entry from etcd
            #       or just set the flag is_active to false

            # session = self.session_mgr.get_session(session_id)
            # if not session.is_active:
            #     raise SessionIsNotActiveError(session_id)

            # session.is_active = False
            # self.session_mgr.put_session(session)

            if not self.session_mgr.exists_session(session_id):
                raise SessionDoesNotExistError(session_id)
            # self.session_mgr.delete_session(session_id)

    ###################
    # Account Manager #
    ###################

    def new_account(self, username: str, password: str):
        """Registers a new account

        Creates a new account. Checks that the username is not registered.

        Args:
            username : Accounts username
            password : Accounts password
        """
        with tracer.start_as_current_span("new_account", attributes={"username": username}):

            # TODO: Ask for admin credentials for creating the account.

            # Creates new account and put it to etcd
            account = Account(username, password)
            self.account_mgr.new_account(account)

            logger.info(f"Created new account for {username}")

    ###################
    # Dataset Manager #
    ###################

    def new_dataset(self, username: str, password: str, dataset_name: str):
        """Registers a new dataset

        Validates the account credentials, and creates a new dataset
        associated to the account. It updates the account metadata
        to add access to the new dataset. The dataset name must bu
        unique.

        Args:
            username : Accounts username
            password : Accounts password
            dataset_name: Name of the new dataset. Must be unique.

        Raises:
            Exception('Account is not valid!'): If wrong credentials
        """
        with tracer.start_as_current_span(
            "new_dataset", attributes={"username": username, "dataset_name": dataset_name}
        ):

            # Validates account credentials
            account = self.account_mgr.get_account(username)
            if not account.verify(password):
                raise AccountInvalidCredentialsError(username)

            # Creates new dataset and updates account's list of datasets
            dataset = Dataset(dataset_name, username)
            account.datasets.append(dataset_name)

            # Put new dataset to etcd and updates account metadata
            # Order matters to check that dataset name is not registered
            self.dataset_mgr.new_dataset(dataset)
            self.account_mgr.put_account(account)

            logger.info(f"Created {dataset.name} dataset for {username} account")

    #####################
    # Metaclass Manager #
    #####################

    # TODO: Deprecate it, no need when using class_name instead of class_id
    # def get_metaclass(self, metaclass_id: UUID):
    #     with tracer.start_as_current_span(
    #         "get_metaclass", attributes={"metaclass_id": metaclass_id}
    #     ):
    #         return self.metaclass_mgr.get_metaclass(metaclass_id)

    #####################
    # Dataclay Metadata #
    #####################

    @tracer.start_as_current_span("get_dataclay_id")
    def get_dataclay_id(self) -> UUID:
        dataclay = self.dataclay_mgr.get_dataclay("this")
        return dataclay.id

    @tracer.start_as_current_span("get_num_objects")
    def get_num_objects(self, language):
        all_object_md = self.object_mgr.get_all_object_md(language)
        return len(all_object_md)

    def autoregister_mds(self, id: UUID, hostname: str, port: int, is_this=False):
        """Autoregister Metadata Service"""
        with tracer.start_as_current_span(
            "autoregister_mds",
            attributes={"id": str(id), "hostname": hostname, "port": port, "is_this": is_this},
        ):
            dataclay = Dataclay(id, hostname, port, is_this)
            self.dataclay_mgr.new_dataclay(dataclay)

    # TODO: Check if needed
    def get_dataclay(self, dataclay_id: UUID) -> Dataclay:
        with tracer.start_as_current_span("get_dataclay", attributes={"dataclay_id": dataclay_id}):
            return self.dataclay_mgr.get_dataclay(dataclay_id)

    #####################
    # EE-SL information #
    #####################

    def get_storage_location(self, sl_name: str) -> StorageLocation:
        with tracer.start_as_current_span("get_storage_location", attributes=locals()):
            return self.dataclay_mgr.get_storage_location(sl_name)

    @tracer.start_as_current_span("get_all_execution_environments")
    def get_all_execution_environments(
        self, language: int, get_external=True, from_backend=False
    ) -> dict:
        """Get all execution environments"""
        # TODO: get_external should
        # TODO: Use exposed_ip_for_client if not from_backend to hide information?
        return self.dataclay_mgr.get_all_execution_environments(language)

    def autoregister_ee(self, id: UUID, hostname: str, port: int, sl_name: str, lang: int):
        """Autoregister execution environment"""
        with tracer.start_as_current_span("autoregister_ee", attributes=locals()):
            # TODO: Check if ee already exists. If so, update its information.
            # TODO: Check connection to ExecutionEnvironment
            exe_env = ExecutionEnvironment(
                id, hostname, port, sl_name, lang, self.get_dataclay_id()
            )
            self.dataclay_mgr.new_execution_environment(exe_env)
            # TODO: Deploy classes to backend? (better call from ee)
            logger.info(
                f"Autoregistered ee with id={id}, hostname={hostname}, port={port}, sl_name={sl_name}"
            )

    ###################
    # Object Metadata #
    ###################

    def register_object(self, object_md: ObjectMetadata, session_id: UUID = None):
        with tracer.start_as_current_span(
            "register_object", attributes={"object_id": object_md.id}
        ):
            # NOTE: If only EE can register objects, no need to check session
            # Checks that session exists and is active
            # session = self.session_mgr.get_session(session_id)
            # if not session.is_active:
            #     raise SessionIsNotActiveError(session_id)

            # NOTE: If a session can just access one dataset, then this
            # dataset will always be the session's default dataset.
            # object_md.dataset_name = session.dataset_name

            self.object_mgr.register_object(object_md)

    # NOTE: It should be used to update synchronously the metadata, not only
    # when the service shutdowns
    def update_object(self, object_md: ObjectMetadata, session_id: UUID = None):
        with tracer.start_as_current_span("update_object", attributes={"object_id": object_md.id}):
            # NOTE: If only EE can update objects, no need to check session
            # Checks that session exists and is active
            # session = self.session_mgr.get_session(session_id)
            # if not session.is_active:
            #     raise SessionIsNotActiveError(session_id)

            # NOTE: If a session can just access one dataset, then this
            # dataset will always be the session's default dataset.
            # object_md.dataset_name = session.dataset_name

            self.object_mgr.update_object(object_md)

    def get_object_md_by_id(
        self, object_id: UUID, session_id=None, check_session=False
    ) -> ObjectMetadata:
        with tracer.start_as_current_span(
            "get_object_md_by_id", attributes={"object_id": object_id}
        ):
            if check_session:
                session = self.session_mgr.get_session(session_id)
                if not session.is_active:
                    raise SessionIsNotActiveError(session_id)

            object_md = self.object_mgr.get_object_md(object_id)
            return object_md

    def get_object_md_by_alias(
        self, alias_name: str, dataset_name: str, session_id: UUID = None, check_session=False
    ):
        with tracer.start_as_current_span(
            "get_object_md_by_alias",
            attributes={
                "alias_name": alias_name,
                "dataset_name": dataset_name,
            },
        ):
            if check_session:
                # Checks that session exists and is active
                session = self.session_mgr.get_session(session_id)
                if not session.is_active:
                    raise SessionIsNotActiveError(session_id)

                # Checks that datset_name is empty or equal to session's dataset
                if not dataset_name:
                    dataset_name = session.dataset_name
                elif dataset_name != session.dataset_name:
                    raise DatasetIsNotAccessibleError(dataset_name, session.username)

            alias = self.object_mgr.get_alias(alias_name, dataset_name)
            object_md = self.object_mgr.get_object_md(alias.object_id)
            return object_md

    def delete_alias(
        self, alias_name: str, dataset_name: str, session_id: UUID, check_session=False
    ):
        with tracer.start_as_current_span(
            "delete_alias",
            attributes={"alias_name": alias_name, "dataset_name": dataset_name},
        ):

            # NOTE: If the session is not checked, we supose the dataset_name is correct
            #       since only the EE is able to set check_session to False
            if check_session:
                # Checks that session exist and is active
                session = self.session_mgr.get_session(session_id)
                if not session.is_active:
                    raise SessionIsNotActiveError(session_id)

                # Check that the dataset_name is the same as session's dataset
                if not dataset_name:
                    dataset_name = session.dataset_name
                elif dataset_name != session.dataset_name:
                    raise DatasetIsNotAccessibleError(dataset_name, session.username)

            self.object_mgr.delete_alias(alias_name, dataset_name)
