from abc import ABC, abstractmethod
from uuid import UUID

import bcrypt

from dataclay.exceptions import *
from dataclay.proto.common import common_pb2
from dataclay.utils.uuid import uuid_to_str
from typing import ClassVar, Literal, Annotated


from pydantic import BaseModel, Field, BeforeValidator

EmptyNone = Annotated[
    None,
    BeforeValidator(lambda x: x if x else None),
]

class KeyValue(BaseModel, ABC):
    @property
    @abstractmethod
    def key(self):
        pass

    @property
    def value(self):
        # return json.dumps(self.__dict__, cls=UUIDEncoder)
        return self.model_dump_json()

    @property
    @abstractmethod
    def path(self):
        pass

    @classmethod
    def from_json(cls, s):
        # return cls(**json.loads(s, object_hook=uuid_parser))
        return cls.model_validate_json(s)

    # NOTE: This is an alternative of "RedisManager.get_kv(...)"
    # @classmethod
    # def from_kv(cls, kv_manager, id):
    #     name = cls.path + id
    #     value = kv_manager.get(name)
    #     if value is None:
    #         raise DoesNotExistError(name)

    #     return cls.from_json(value)


class Dataclay(KeyValue):
    path: ClassVar = "/dataclay/"

    id: UUID
    host: str
    port: int
    is_this: bool = False

    @property
    def key(self):
        return self.path + ("this" if self.is_this else str(id))

    @classmethod
    def from_proto(cls, proto):
        return cls(
            id=proto.id,
            host=proto.host,
            port=proto.port,
            is_this=proto.is_this,
        )

    def get_proto(self):
        # return common_pb2.Dataclay(self.model_dump())
        return common_pb2.Dataclay(
            id=uuid_to_str(self.id),
            host=self.host,
            port=self.port,
            is_this=self.is_this,
        )


class Backend(KeyValue):
    path: ClassVar = "/backend/"

    id: UUID
    host: str
    port: int
    dataclay_id: UUID

    @property
    def key(self):
        return self.path + str(self.id)

    @classmethod
    def from_proto(cls, proto):
        return cls(
            id=proto.id,
            host=proto.host,
            port=proto.port,
            dataclay_id=proto.dataclay_id,
        )

    # TODO: Improve it with __getattributes__ and interface
    def get_proto(self):
        return common_pb2.Backend(
            id=uuid_to_str(self.id),
            host=self.host,
            port=self.port,
            dataclay_id=uuid_to_str(self.dataclay_id),
        )


class ObjectMetadata(KeyValue):
    path: ClassVar = "/object/"

    id: UUID
    dataset_name: str | None
    class_name: str
    master_backend_id: UUID | None
    replica_backend_ids: set
    is_read_only: bool
    original_object_id: UUID | EmptyNone
    versions_object_ids: list[UUID]

    @property
    def key(self):
        return self.path + str(self.id)

    @classmethod
    def from_proto(cls, proto):
        return cls(
            id=proto.id,
            dataset_name=proto.dataset_name,
            class_name=proto.class_name,
            master_backend_id=proto.master_backend_id,
            replica_backend_ids=proto.replica_backend_ids,
            is_read_only=proto.is_read_only,
            original_object_id=proto.original_object_id,
            versions_object_ids=proto.versions_object_ids,
        )

    def get_proto(self):
        return common_pb2.ObjectMetadata(
            id=uuid_to_str(self.id),
            dataset_name=self.dataset_name,
            class_name=self.class_name,
            master_backend_id=uuid_to_str(self.master_backend_id),
            replica_backend_ids=map(uuid_to_str, self.replica_backend_ids),
            is_read_only=self.is_read_only,
            original_object_id=uuid_to_str(self.original_object_id),
            versions_object_ids=map(uuid_to_str, self.versions_object_ids),
        )


class Alias(KeyValue):
    path: ClassVar = "/alias/"

    name: str
    dataset_name: str
    object_id: UUID

    @property
    def key(self):
        return self.path + f"{self.dataset_name}/{self.name}"

    @classmethod
    def from_proto(cls, proto):
        return cls(
            name=proto.name, dataset_name=proto.dataset_name, object_id=proto.object_id
        )

    def get_proto(self):
        return common_pb2.Alias(
            name=self.name,
            dataset_name=self.dataset_name,
            object_id=uuid_to_str(self.object_id),
        )


class Session(KeyValue):
    path: ClassVar = "/session/"

    id: UUID
    username: str
    dataset_name: str
    is_active: bool = True

    @property
    def key(self):
        return self.path + str(self.id)

    @classmethod
    def from_proto(cls, proto):
        return cls(id=proto.id, username=proto.username, dataset_name=proto.dataset_name, is_active=proto.is_active)

    def get_proto(self):
        return common_pb2.Session(
            id=uuid_to_str(self.id),
            username=self.username,
            dataset_name=self.dataset_name,
            is_active=self.is_active,
        )


class Account(KeyValue):
    path: ClassVar = "/account/"

    username: str
    hashed_password: str = None
    role: str = "NORMAL"
    datasets: list = Field(default_factory=list)

    # def __post_init__(self):
    #     self.datasets = set(self.datasets)

    @property
    def key(self):
        return self.path + self.username

    @classmethod
    def new(cls, username, password, role="NORMAL", datasets=None):
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        datasets = datasets or []
        return cls(username=username, hashed_password=hashed_password, role=role, datasets=datasets)

    def verify(self, password, role=None):
        if not bcrypt.checkpw(password.encode(), self.hashed_password.encode()):
            return False
        if role is not None and self.role != role:
            return False
        return True


class Dataset(KeyValue):
    path: ClassVar = "/dataset/"

    name: str
    owner: str
    is_public: bool = False

    @property
    def key(self):
        return self.path + self.name
