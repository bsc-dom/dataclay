import logging
import uuid
from uuid import UUID

from dataclay.exceptions.exceptions import *
from dataclay.metadata.kvdata import (
    Account,
    Alias,
    Backend,
    Dataclay,
    Dataset,
    ObjectMetadata,
    Session,
)
from dataclay.metadata.redismanager import RedisManager
from dataclay.utils.telemetry import trace

FEDERATOR_ACCOUNT_USERNAME = "Federator"
EXTERNAL_OBJECTS_DATASET_NAME = "ExternalObjects"


# Acquire a tracer and logger
tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)


class MetadataAPI:
    def __init__(self, kv_host, kv_port):
        self.kv_manager = RedisManager(kv_host, kv_port)

        logger.info("Initialized MetadataService")

    def is_ready(self, timeout=None, pause=0.5):
        return self.kv_manager.is_ready(timeout=timeout, pause=pause)

    ###########
    # Session #
    ###########

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

    ###########
    # Account #
    ###########

    @tracer.start_as_current_span("new_superuser")
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

    @tracer.start_as_current_span("new_account")
    def new_account(self, username: str, password: str):
        """Registers a new account

        Creates a new account. Checks that the username is not registered.

        Args:
            username : Accounts username
            password : Accounts password
        """
        # TODO: Ask for admin credentials for creating the account.

        # Creates new account and put it to etcd
        account = Account.new(username, password)
        self.kv_manager.set_new(account)

        logger.info(f"Created new account for {username}")

    ###########
    # Dataset #
    ###########

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

    ############
    # Dataclay #
    ############

    @tracer.start_as_current_span("new_dataclay")
    def new_dataclay(self, dataclay_id, hostname, port, is_this=False):
        dataclay = Dataclay(dataclay_id, hostname, port, is_this)
        self.kv_manager.set_new(dataclay)

    @tracer.start_as_current_span("get_dataclay")
    def get_dataclay(self, dataclay_id: UUID | str) -> Dataclay:
        return self.kv_manager.get_kv(Dataclay, dataclay_id)

    ###########
    # Backend #
    ###########

    @tracer.start_as_current_span("get_all_backends")
    def get_all_backends(self, from_backend=False) -> dict:
        result = self.kv_manager.getprefix(Backend, "/backend/")
        return {UUID(k): v for k, v in result.items()}

    @tracer.start_as_current_span("register_backend")
    def register_backend(self, id: UUID, hostname: str, port: int, dataclay_id: UUID):
        backend = Backend(id, hostname, port, dataclay_id)
        self.kv_manager.set_new(backend)
        logger.info(f"Registered new backend with id={id}, hostname={hostname}, port={port}")

    @tracer.start_as_current_span("delete_backend")
    def delete_backend(self, id: UUID):
        self.kv_manager.delete_kv(Backend.path + str(id))

    ###################
    # Dataclay Object #
    ###################

    @tracer.start_as_current_span("get_all_objects")
    def get_all_objects(self):
        result = self.kv_manager.getprefix(ObjectMetadata, "/object/")
        return result

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

        self.kv_manager.set(object_md)

    @tracer.start_as_current_span("change_object_id")
    def change_object_id(self, old_id: UUID, new_id: UUID):
        object_md = self.kv_manager.getdel_kv(ObjectMetadata, old_id)
        object_md.id = new_id
        self.kv_manager.set(object_md)

    @tracer.start_as_current_span("delete_object")
    def delete_object(self, id: UUID):
        self.kv_manager.delete_kv(ObjectMetadata.path + str(id))

    @tracer.start_as_current_span("get_object_md_by_id")
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

    #########
    # Alias #
    #########

    @tracer.start_as_current_span("new_alias")
    def new_alias(
        self,
        alias_name: str,
        dataset_name: str,
        object_id: UUID,
        session_id: UUID,
        check_session=False,
    ):
        alias = Alias(alias_name, dataset_name, object_id)
        self.kv_manager.set_new(alias)

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

        with self.kv_manager.lock(ObjectMetadata.path + str(alias.object_id)):
            object_md = self.kv_manager.get_kv(ObjectMetadata, alias.object_id)

            # Remove alias from object metadata
            object_md.alias_name = None
            self.kv_manager.set(object_md)
