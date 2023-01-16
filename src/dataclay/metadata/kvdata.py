import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from uuid import UUID

from passlib.hash import bcrypt

from dataclay.exceptions import *
from dataclay.protos import common_messages_pb2
from dataclay.utils.json import UUIDEncoder, uuid_parser


class KeyValue(ABC):
    @property
    @abstractmethod
    def key(self):
        pass

    @property
    def value(self):
        return json.dumps(self.__dict__, cls=UUIDEncoder)

    @property
    @abstractmethod
    def path(self):
        pass

    @classmethod
    def from_json(cls, s):
        return cls(**json.loads(s, object_hook=uuid_parser))

    # NOTE: This is an alternative of "RedisManager.get_kv(...)"
    # @classmethod
    # def from_kv(cls, kv_manager, id):
    #     name = cls.path + id
    #     value = kv_manager.get(name)
    #     if value is None:
    #         raise DoesNotExistError(name)

    #     return cls.from_json(value)


@dataclass
class Dataclay(KeyValue):

    path = "/dataclay/"

    id: UUID
    hostname: str
    port: int
    is_this: bool = False

    @property
    def key(self):
        return self.path + ("this" if self.is_this else str(id))

    @classmethod
    def from_proto(cls, proto):
        return cls(
            UUID(proto.id),
            proto.hostname,
            proto.port,
            proto.is_this,
        )

    def get_proto(self):
        return common_messages_pb2.Dataclay(
            id=str(self.id),
            hostname=self.hostname,
            port=self.port,
            is_this=self.is_this,
        )


@dataclass
class Backend(KeyValue):

    path = "/backend/"

    id: UUID
    hostname: str
    port: int
    dataclay_id: UUID

    @property
    def key(self):
        return self.path + str(self.id)

    @classmethod
    def from_proto(cls, proto):
        return cls(
            UUID(proto.id),
            proto.hostname,
            proto.port,
            UUID(proto.dataclay_id),
        )

    # TODO: Improve it with __getattributes__ and interface
    def get_proto(self):
        return common_messages_pb2.Backend(
            id=str(self.id),
            hostname=self.hostname,
            port=self.port,
            dataclay_id=str(self.dataclay_id),
        )


@dataclass
class ObjectMetadata(KeyValue):

    path = "/object/"

    id: UUID = None
    alias_name: str = None
    dataset_name: str = None
    class_name: UUID = None
    backend_id: UUID = None
    replica_backend_ids: UUID = None
    language: str = None
    is_read_only: bool = False

    @property
    def key(self):
        return self.path + str(self.id)

    @classmethod
    def from_proto(cls, proto):
        return cls(
            UUID(proto.id),
            proto.alias_name if proto.alias_name != "" else None,
            proto.dataset_name,
            proto.class_name,
            UUID(proto.backend_id),
            list(map(UUID, proto.replica_backend_ids)),
            proto.language,
            proto.is_read_only,
        )

    def get_proto(self):
        return common_messages_pb2.ObjectMetadata(
            id=str(self.id),
            alias_name=self.alias_name,
            dataset_name=self.dataset_name,
            class_name=self.class_name,
            backend_id=str(self.backend_id),
            replica_backend_ids=list(map(str, self.replica_backend_ids)),
            language=self.language,
            is_read_only=self.is_read_only,
        )


@dataclass
class Alias(KeyValue):

    path = "/alias/"

    name: str
    dataset_name: str
    object_id: UUID

    @property
    def key(self):
        return self.path + f"{self.dataset_name}/{self.name}"


@dataclass
class Session(KeyValue):

    path = "/session/"

    id: UUID
    username: str
    dataset_name: str
    is_active: bool = True

    @property
    def key(self):
        return self.path + str(self.id)

    @classmethod
    def from_proto(cls, proto):
        return cls(UUID(proto.id), proto.username, proto.dataset_name, proto.is_active)

    def get_proto(self):
        return common_messages_pb2.Session(
            id=str(self.id),
            username=self.username,
            dataset_name=self.dataset_name,
            is_active=self.is_active,
        )


@dataclass
class Account(KeyValue):

    path = "/account/"

    username: str
    hashed_password: str = None
    role: str = "NORMAL"
    datasets: list = field(default_factory=list)

    # def __post_init__(self):
    #     self.datasets = set(self.datasets)

    @property
    def key(self):
        return self.path + self.username

    @classmethod
    def new(cls, username, password, role="NORMAL", datasets=None):
        hashed_password = bcrypt.hash(password)
        datasets = datasets or []
        return cls(username, hashed_password, role, datasets)

    def verify(self, password, role=None):
        if not bcrypt.verify(password, self.hashed_password):
            return False
        if role is not None and self.role != role:
            return False
        return True


@dataclass
class Dataset(KeyValue):

    path = "/dataset/"

    name: str
    owner: str
    is_public: bool = False

    @property
    def key(self):
        return self.path + self.name
