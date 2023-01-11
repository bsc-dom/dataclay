import logging
import uuid
from uuid import UUID

import etcd3
import redis
import grpc
from opentelemetry import trace
from dataclay.metadata.managers.kvmanager import KVManager

from dataclay.exceptions.exceptions import *
from dataclay.metadata.managers.dataclay import (
    Backend,
    Dataclay,
    DataclayManager,
    StorageLocation,
)
from dataclay.metadata.managers.kvdata import Dataset, Account, Session, ObjectMetadata, Alias

FEDERATOR_ACCOUNT_USERNAME = "Federator"
EXTERNAL_OBJECTS_DATASET_NAME = "ExternalObjects"


# Acquire a tracer and logger
tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)


class MetadataAPI:
    def __init__(self, etcd_host, etcd_port):
        # Creates etcd client
        self.kv_client = etcd3.client(etcd_host, etcd_port)
        self.r_kv_client = redis.Redis(decode_responses=True)

        # Creates managers for each class
        self.dataclay_mgr = DataclayManager(self.kv_client)
        self.kv_manager = KVManager(self.r_kv_client)

        logger.info("Initialized MetadataService")

    def is_ready(self, timeout=None):
        try:
            grpc.channel_ready_future(self.kv_client.channel).result(timeout)
            return True
        except grpc.FutureTimeoutError:
            return False

    ###################
    # Session Manager #
    ###################

    @tracer.start_as_current_span("new_session")
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

        # Validates account credentials
        account = self.kv_manager.get_kv(Account, username)

        if not account.verify(password):
            raise AccountInvalidCredentialsError(username)

        # Validates accounts access to dataset_name
        dataset = self.kv_manager.get_kv(Dataset, dataset_name)

        if not dataset.is_public and dataset_name not in account.datasets:
            raise DatasetIsNotAccessibleError(dataset_name, username)

        # Creates a new session
        session = Session(uuid.uuid4(), username, dataset_name)
        self.kv_manager.set(session)

        logger.info(f"Created new session for {username} with id {session.id}")
        return session

    @tracer.start_as_current_span("get_session")
    def get_session(self, session_id: UUID) -> Session:
        return self.kv_manager.get_kv(Session, session_id)

    @tracer.start_as_current_span("close_session")
    def close_session(self, session_id: UUID):
        # TODO: decide if close session remove the entry from etcd
        #       or just set the flag is_active to false

        # session = self.session_mgr.get_session(session_id)
        # if not session.is_active:
        #     raise SessionIsNotActiveError(session_id)

        # session.is_active = False
        # self.session_mgr.put_session(session)

        # if not self.session_mgr.exists_session(session_id):
        #     raise SessionDoesNotExistError(session_id)
        # self.session_mgr.delete_session(session_id)
        pass

    ###################
    # Account Manager #
    ###################

    def new_superuser(self, username: str, password: str, dataset_name: str):
        # Creates new account and put it to etcd
        account = Account.new(username, password, role="ADMIN")

        # Creates new dataset and updates account's list of datasets
        dataset = Dataset(dataset_name, username)
        account.datasets.append(dataset_name)

        # Put new dataset and account to etcd
        # Order matters to check that dataset name is not registered
        self.kv_manager.set_new(dataset)
        self.kv_manager.set_new(account)

        logger.info(f"Created new account for {username} with dataset {dataset.name}")

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
            account = Account.new(username, password)
            self.kv_manager.set_new(account)

            logger.info(f"Created new account for {username}")

    ###################
    # Dataset Manager #
    ###################

    @tracer.start_as_current_span("new_dataset")
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

        # Lock to update account.datasets without race condition
        with self.kv_manager.lock(Account.path + username):

            # Validates account credentials
            account = self.kv_manager.get_kv(Account, username)
            if not account.verify(password):
                raise AccountInvalidCredentialsError(username)

            # Creates new dataset and updates account's list of datasets
            dataset = Dataset(dataset_name, username)
            account.datasets.append(dataset_name)

            # Put new dataset to kv and updates account metadata
            # Order matters to check that dataset name is not registered
            self.kv_manager.set_new(dataset)
            self.kv_manager.update(account)

            logger.info(f"Created {dataset.name} dataset for {username} account")

    #####################
    # Dataclay Metadata #
    #####################

    @tracer.start_as_current_span("get_dataclay_id")
    def get_dataclay_id(self) -> UUID:
        dataclay_id = self.dataclay_mgr.get_dataclay_id()
        return dataclay_id

    @tracer.start_as_current_span("put_dataclay_id")
    def put_dataclay_id(self, dataclay_id) -> UUID:
        self.dataclay_mgr.put_dataclay_id(dataclay_id)

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
            # TODO: Check connection to Backend
            exe_env = Backend(id, hostname, port, sl_name, lang, self.get_dataclay_id())
            self.dataclay_mgr.new_execution_environment(exe_env)

            logger.info(
                f"Autoregistered ee with id={id}, hostname={hostname}, port={port}, sl_name={sl_name}"
            )

    ###################
    # Object Metadata #
    ###################

    @tracer.start_as_current_span("register_object")
    def register_object(self, object_md: ObjectMetadata, session_id: UUID = None):
        # NOTE: If only EE can register objects, no need to check session
        # Checks that session exists and is active
        # session = self.session_mgr.get_session(session_id)
        # if not session.is_active:
        #     raise SessionIsNotActiveError(session_id)

        # NOTE: If a session can just access one dataset, then this
        # dataset will always be the session's default dataset.
        # object_md.dataset_name = session.dataset_name

        if object_md.alias_name:
            alias = Alias(object_md.alias_name, object_md.dataset_name, object_md.id)
            self.kv_manager.set_new(alias)

        self.kv_manager.set_new(object_md)

    @tracer.start_as_current_span("start_as_current_span")
    def get_object_md_by_id(self, object_id: UUID, session_id=None, check_session=False):
        if check_session:
            session = self.kv_manager.get_kv(Session, session_id)
            if not session.is_active:
                raise SessionIsNotActiveError(session_id)

        object_md = self.kv_manager.get_kv(ObjectMetadata, object_id)
        return object_md

    @tracer.start_as_current_span("get_object_md_by_alias")
    def get_object_md_by_alias(
        self, alias_name: str, dataset_name: str, session_id: UUID = None, check_session=False
    ):
        if check_session:
            # Checks that session exists and is active
            session = self.kv_manager.get_kv(Session, session_id)
            if not session.is_active:
                raise SessionIsNotActiveError(session_id)

            # Checks that datset_name is empty or equal to session's dataset
            if not dataset_name:
                dataset_name = session.dataset_name
            elif dataset_name != session.dataset_name:
                raise DatasetIsNotAccessibleError(dataset_name, session.username)

        alias = self.kv_manager.get_kv(Alias, f"{dataset_name}/{alias_name}")
        return self.kv_manager.get_kv(ObjectMetadata, alias.object_id)

    @tracer.start_as_current_span("delete_alias")
    def delete_alias(
        self, alias_name: str, dataset_name: str, session_id: UUID, check_session=False
    ):

        # NOTE: If the session is not checked, we supose the dataset_name is correct
        #       since only the EE is able to set check_session to False
        if check_session:
            # Checks that session exist and is active
            session = self.kv_manager.get_kv(Session, session_id)
            if not session.is_active:
                raise SessionIsNotActiveError(session_id)

            # Check that the dataset_name is the same as session's dataset
            if not dataset_name:
                dataset_name = session.dataset_name
            elif dataset_name != session.dataset_name:
                raise DatasetIsNotAccessibleError(dataset_name, session.username)

        alias = self.kv_manager.getdel_kv(Alias, f"{dataset_name}/{alias_name}")

        with self.kv_manager.lock(ObjectMetadata.path + alias.object_id):
            object_md = self.kv_manager.get_kv(ObjectMetadata, alias.object_id)

            # Remove alias from object metadata
            object_md.alias_name = None
            self.kv_manager.set(object_md)
