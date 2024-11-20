import logging
from typing import Callable, Optional, Union
from uuid import UUID

from dataclay.exceptions import (
    AccountError,
    AccountInvalidCredentialsError,
    AliasAlreadyExistError,
    AliasDoesNotExistError,
    AlreadyExistError,
)
from dataclay.metadata.kvdata import (
    Account,
    Alias,
    Backend,
    Dataclay,
    Dataset,
    ObjectMetadata,
)
from dataclay.metadata.redismanager import RedisManager
from dataclay.utils.telemetry import trace

FEDERATOR_ACCOUNT_USERNAME = "Federator"
EXTERNAL_OBJECTS_DATASET_NAME = "ExternalObjects"


# Acquire a tracer and logger
tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)


class MetadataAPI:
    def __init__(self, kv_host: str, kv_port: int):
        self.kv_manager = RedisManager(kv_host, kv_port)

    async def close(self):
        await self.kv_manager.close()

    async def is_ready(self, timeout: Optional[float] = None, pause: float = 0.5):
        return await self.kv_manager.is_ready(timeout=timeout, pause=pause)

    ###########
    # Account #
    ###########

    @tracer.start_as_current_span("new_superuser")
    async def new_superuser(self, username: str, password: str, dataset_name: str):
        logger.debug("Creating new superuser with name=%s, dataset=%s", username, dataset_name)
        # Creates new account and put it to etcd
        account = Account.new(username, password, role="ADMIN")

        # Creates new dataset and updates account's list of datasets
        dataset = Dataset(name=dataset_name, owner=username)
        account.datasets.append(dataset_name)

        # Put new dataset and account to etcd
        # Order matters to check that dataset name is not registered
        await self.kv_manager.set_new(dataset)
        await self.kv_manager.set_new(account)
        logger.info("New superuser with name=%s, dataset=%s", username, dataset.name)

    @tracer.start_as_current_span("new_account")
    async def new_account(self, username: str, password: str):
        """Registers a new account

        Creates a new account. Checks that the username is not registered.

        Args:
            username : Accounts username
            password : Accounts password
        """
        logger.debug("Creating new account with name=%s", username)
        # TODO: Ask for admin credentials for creating the account.

        # Creates new account and put it to etcd
        account = Account.new(username, password)
        await self.kv_manager.set_new(account)
        logger.info("New account with name=%s", username)

    ###########
    # Dataset #
    ###########

    @tracer.start_as_current_span("new_dataset")
    async def new_dataset(self, username: str, password: str, dataset_name: str):
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
        logger.debug("Creating new dataset with name=%s, owner=%s", dataset_name, username)
        # Lock to update account.datasets without race condition
        with await self.kv_manager.lock(Account.path + username):
            # Validates account credentials
            account = await self.kv_manager.get_kv(Account, username)
            if not account.verify(password):
                raise AccountInvalidCredentialsError(username)

            # Creates new dataset and updates account's list of datasets
            dataset = Dataset(name=dataset_name, owner=username)
            account.datasets.append(dataset_name)

            # Put new dataset to kv and updates account metadata
            # Order matters to check that dataset name is not registered
            await self.kv_manager.set_new(dataset)
            await self.kv_manager.update(account)
            logger.info("New dataset with name=%s, owner=%s", dataset_name, username)

    @tracer.start_as_current_span("add_account_to_dataset")
    async def add_account_to_dataset(
        self, username: str, password: str, dataset_name: str, account_name: str
    ):
        """Allow a certain account to access a certain dataset.

        The owner of a dataset can call this and add access to an arbitrary account.
        """
        logger.debug("Adding account %s to dataset %s", account_name, dataset_name)
        with await self.kv_manager.lock(Account.path + account_name):
            operating_acc = await self.kv_manager.get_kv(Account, username)
            if not operating_acc.verify(password):
                raise AccountInvalidCredentialsError(username)

            # TODO: gather
            dataset = await self.kv_manager.get_kv(Dataset, dataset_name)
            if dataset.owner != username:
                raise AccountError(username)

            account = await self.kv_manager.get_kv(Account, account_name)
            account.datasets.append(dataset_name)
            await self.kv_manager.update(account)
            logger.info("Added dataset %s to account %s", dataset_name, account_name)

    ############
    # Dataclay #
    ############

    @tracer.start_as_current_span("new_dataclay")
    async def new_dataclay(self, dataclay_id: UUID, host: str, port: int, is_this: bool = False):
        logger.debug("Registering Dataclay with id %s, host %s, port %s", dataclay_id, host, port)
        dataclay = Dataclay(id=dataclay_id, host=host, port=port, is_this=is_this)
        await self.kv_manager.set_new(dataclay)
        logger.info(
            "Registered MetadataService with id=%s, host=%s, port=%s", dataclay_id, host, port
        )

    @tracer.start_as_current_span("get_dataclay")
    async def get_dataclay(self, dataclay_id: Union[UUID, str]) -> Dataclay:
        logger.debug("Getting Dataclay with id %s", dataclay_id)
        return await self.kv_manager.get_kv(Dataclay, dataclay_id)

    ###########
    # Backend #
    ###########

    @tracer.start_as_current_span("get_all_backends")
    async def get_all_backends(self, from_backend: bool = False, **kwargs) -> dict[UUID, Backend]:
        logger.debug("Getting all backends from kv store")
        result = await self.kv_manager.getprefix(Backend, "/backend/")
        return {UUID(k): v for k, v in result.items()}

    @tracer.start_as_current_span("register_backend")
    async def register_backend(self, id: UUID, host: str, port: int, dataclay_id: UUID):
        logger.debug("Registering Backend with id %s, host %s, port %s", id, host, port)
        backend = Backend(id=id, host=host, port=port, dataclay_id=dataclay_id)
        await self.kv_manager.set_new(backend)
        logger.info("Registered Backend with id=%s, host=%s, port=%s", id, host, port)

        # Publishes a message to the channel "new-backend-client"
        await self.kv_manager.publish("new-backend-client", backend.value)

    @tracer.start_as_current_span("delete_backend")
    async def delete_backend(self, id: UUID):
        logger.debug("Deleting Backend with id %s", id)
        await self.kv_manager.delete_kv(Backend.path + str(id))
        logger.info("Deleted Backend with id=%s", id)

        # Publishes a message to the channel "del-backend-clients"
        await self.kv_manager.publish("del-backend-client", str(id))

    ###################
    # Dataclay Object #
    ###################

    @tracer.start_as_current_span("get_all_objects")
    async def get_all_objects(
        self, filter_func: Optional[Callable[[ObjectMetadata], bool]] = None
    ) -> dict[UUID, ObjectMetadata]:
        logger.debug("Getting all objects from kv store")
        result = await self.kv_manager.getprefix(ObjectMetadata, "/object/")

        if filter_func is None:
            # No filter function provided, return all results
            return {UUID(k): v for k, v in result.items()}

        # Apply filter function to results
        return {UUID(k): v for k, v in result.items() if filter_func(v)}

    @tracer.start_as_current_span("upsert_object")
    async def upsert_object(self, object_md: ObjectMetadata):
        logger.debug("Upserting object with id %s", object_md.id)
        await self.kv_manager.set(object_md)

    @tracer.start_as_current_span("change_object_id")
    async def change_object_id(self, old_id: UUID, new_id: UUID):
        logger.debug("Changing object id from %s to %s", old_id, new_id)
        object_md = await self.kv_manager.getdel_kv(ObjectMetadata, old_id)
        object_md.id = new_id
        await self.kv_manager.set(object_md)

    @tracer.start_as_current_span("delete_object")
    async def delete_object(self, id: UUID):
        logger.debug("Deleting object with id %s", id)
        await self.kv_manager.delete_kv(ObjectMetadata.path + str(id))

    @tracer.start_as_current_span("get_object_md_by_id")
    async def get_object_md_by_id(self, object_id: UUID) -> ObjectMetadata:
        logger.debug("Getting object metadata with id %s", object_id)
        object_md = await self.kv_manager.get_kv(ObjectMetadata, object_id)
        return object_md

    @tracer.start_as_current_span("get_object_md_by_alias")
    async def get_object_md_by_alias(
        self,
        alias_name: str,
        dataset_name: str,
    ) -> ObjectMetadata:
        logger.debug("Getting object metadata with alias='%s.%s'", dataset_name, alias_name)
        alias = await self.kv_manager.get_kv(Alias, f"{dataset_name}/{alias_name}")
        return await self.kv_manager.get_kv(ObjectMetadata, alias.object_id)

    #########
    # Alias #
    #########

    @tracer.start_as_current_span("new_alias")
    async def new_alias(
        self,
        alias_name: str,
        dataset_name: str,
        object_id: UUID,
    ):
        logger.debug(
            "Creating new alias '%s.%s' for object %s", dataset_name, alias_name, object_id
        )
        alias = Alias(name=alias_name, dataset_name=dataset_name, object_id=object_id)
        try:
            await self.kv_manager.set_new(alias)
        except AlreadyExistError as e:
            raise AliasAlreadyExistError(alias_name, dataset_name) from e

    @tracer.start_as_current_span("get_all_alias")
    async def get_all_alias(
        self, dataset_name: Optional[str] = None, object_id: Optional[UUID] = None
    ) -> dict[str, Alias]:
        logger.debug("Getting all aliases dataset=%s, object=%s", dataset_name, object_id)
        prefix = "/alias/"
        if dataset_name:
            prefix = prefix + dataset_name + "/"

        result = await self.kv_manager.getprefix(Alias, prefix)
        return {k: v for k, v in result.items() if v.object_id == object_id or not object_id}

    @tracer.start_as_current_span("delete_alias")
    async def delete_alias(
        self,
        alias_name: str,
        dataset_name: str,
    ):
        logger.debug("Deleting alias '%s.%s'", dataset_name, alias_name)
        await self.kv_manager.delete_kv(Alias.path + f"{dataset_name}/{alias_name}")
