import json
import uuid

from dataclay.exceptions.exceptions import *
from dataclay_common.protos import common_messages_pb2
from dataclay_common.protos.common_messages_pb2 import LANG_NONE
from dataclay.utils.json import UUIDEncoder, uuid_parser


class ObjectMetadata:

    # __slots__ = (
    #     "id",
    #     "alias_name",
    #     "dataset_name",
    #     "class_id",
    #     "master_ee_id",
    #     "replica_ee_ids",
    #     "language",
    #     "is_read_only",
    # )

    def __init__(
        self,
        id=None,
        alias_name=None,
        dataset_name=None,
        class_name=None,
        master_ee_id=None,
        replica_ee_ids=None,
        language=None,
        is_read_only=False,
    ):
        self.id = id
        self.alias_name = alias_name
        self.dataset_name = dataset_name
        self.class_name = class_name
        self.master_ee_id = master_ee_id
        self.replica_ee_ids = replica_ee_ids
        self.language = language
        self.is_read_only = is_read_only

    def key(self):
        return f"/object/{self.id}"

    def value(self):
        return json.dumps(self.__dict__, cls=UUIDEncoder)

    @classmethod
    def from_json(cls, s):
        return cls(**json.loads(s, object_hook=uuid_parser))

    @classmethod
    def from_proto(cls, proto):
        object_md = cls(
            uuid.UUID(proto.id),
            proto.alias_name,
            proto.dataset_name,
            proto.class_name,
            uuid.UUID(proto.master_ee_id),
            list(map(uuid.UUID, proto.replica_ee_ids)),
            proto.language,
            proto.is_read_only,
        )
        return object_md

    def get_proto(self):
        return common_messages_pb2.ObjectMetadata(
            id=str(self.id),
            alias_name=self.alias_name,
            dataset_name=self.dataset_name,
            class_name=self.class_name,
            master_ee_id=str(self.master_ee_id),
            replica_ee_ids=list(map(str, self.replica_ee_ids)),
            language=self.language,
            is_read_only=self.is_read_only,
        )


class Alias:
    def __init__(self, name, dataset_name, object_id):
        """Return an instance of an Alias"""
        self.name = name
        self.dataset_name = dataset_name
        self.object_id = object_id

    def key(self):
        return f"/alias/{self.dataset_name}/{self.name}"

    def value(self):
        return json.dumps(self.__dict__, cls=UUIDEncoder)

    @classmethod
    def from_json(cls, s):
        return cls(**json.loads(s, object_hook=uuid_parser))


class ObjectManager:

    lock = "lock_object"

    def __init__(self, etcd_client):
        self.etcd_client = etcd_client

    def register_object(self, object_md):
        # Store alias (if not none nor empty) and object_md to etcd
        if object_md.alias_name:
            alias = Alias(object_md.alias_name, object_md.dataset_name, object_md.id)
            self.new_alias(alias)

        self.etcd_client.put(object_md.key(), object_md.value())

    # NOTE: The update should be done by field, not all object_md at once
    def update_object(self, object_md):
        # Update object metadata

        old_object_md = self.get_object_md(object_md.id)

        # NOTE: If only one dataset per session, it should never be different
        #       ¿Remove the check?
        if object_md.dataset_name != old_object_md.dataset_name:
            raise Exception(
                f"New object dataset ({object_md.dataset_name}) is different from previous one ({old_object_md.dataset_name})"
            )

        if object_md.language != old_object_md.language:
            raise Exception(
                f"New object language ({object_md.language}) is different from previous one ({old_object_md.language})"
            )

        if object_md.class_name != old_object_md.class_name:
            raise Exception(
                f"New object class_name ({object_md.class_name}) is different from previous one ({old_object_md.class_name})"
            )

        if object_md.alias_name and old_object_md.alias_name != object_md.alias_name:
            # Remove the old alias and create the new alias
            if old_object_md.alias_name:
                alias_key = f"/alias/{old_object_md.dataset_name}/{old_object_md.alias_name}"
                self.etcd_client.delete(alias_key)

            alias = Alias(object_md.alias_name, object_md.dataset_name, object_md.id)
            self.new_alias(alias)

        self.etcd_client.put(object_md.key(), object_md.value())

    def put(self, o):
        self.etcd_client.put(o.key(), o.value())

    def get_alias(self, alias_name, dataset_name):
        # Get dataset from etcd and checks that it exists
        key = f"/alias/{dataset_name}/{alias_name}"
        value = self.etcd_client.get(key)[0]
        if value is None:
            raise AliasDoesNotExistError(alias_name, dataset_name)

        return Alias.from_json(value)

    def get_object_md(self, object_id):
        # Get dataset from etcd and checks that it exists
        key = f"/object/{object_id}"
        value = self.etcd_client.get(key)[0]
        if value is None:
            raise ObjectDoesNotExistError(object_id)

        return ObjectMetadata.from_json(value)

    def new_alias(self, alias):
        """Creates a new alias and checks that the alias doesn't exists"""

        with self.etcd_client.lock(self.lock):
            if self.etcd_client.get(alias.key())[0] is not None:
                raise AliasAlreadyExistError(alias.name, alias.dataset_name)
            self.put(alias)

    def delete_alias(self, alias_name, dataset_name):

        alias = self.get_alias(alias_name, dataset_name)
        object_md = self.get_object_md(alias.object_id)

        # Remove alias from object metadata
        object_md.alias_name = None
        self.put(object_md)

        # Remove alias metadata
        self.etcd_client.delete(alias.key())

    def get_all_object_md(self, language=None):
        """Get all objects_md"""
        prefix = "/object/"
        values = self.etcd_client.get_prefix(prefix)

        all_object_md = dict()
        for value, metadata in values:
            key = metadata.key.decode().split("/")[-1]
            object_md = ObjectMetadata.from_json(value)
            if language is None or language == LANG_NONE or object_md.language == language:
                all_object_md[uuid.UUID(key)] = object_md
        return all_object_md
