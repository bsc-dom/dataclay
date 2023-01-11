import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from passlib.hash import bcrypt

from dataclay.protos import common_messages_pb2
from uuid import UUID
from dataclay.exceptions import *
from dataclay.utils.json import UUIDEncoder, uuid_parser


class KeyValue(ABC):
    @property
    @abstractmethod
    def key(self):
        pass

    @property
    @abstractmethod
    def value(self):
        pass

    @property
    @abstractmethod
    def path(self):
        pass

    @classmethod
    def from_json(cls, s):
        return cls(**json.loads(s, object_hook=uuid_parser))

    # NOTE: This is an alternative of "KVManager.get_kv(...)"
    # @classmethod
    # def from_kv(cls, kv_manager, id):
    #     name = cls.path + id
    #     value = kv_manager.get(name)
    #     if value is None:
    #         raise DoesNotExistError(name)

    #     return cls.from_json(value)


@dataclass
class Session(KeyValue):

    path = "/session/"

    id: UUID
    username: str
    dataset_name: str
    is_active: bool = True

    @property
    def key(self):
        return f"/session/{self.id}"

    @property
    def value(self):
        return json.dumps(self.__dict__, cls=UUIDEncoder)

    @classmethod
    def from_proto(cls, proto):
        session = cls(
            UUID(proto.id),
            proto.username,
            proto.dataset_name,
            proto.is_active,
        )
        return session

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
        return f"/account/{self.username}"

    @property
    def value(self):
        return json.dumps(self.__dict__, cls=UUIDEncoder)

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
        return f"/dataset/{self.name}"

    @property
    def value(self):
        return json.dumps(self.__dict__, cls=UUIDEncoder)

    @classmethod
    def from_json(cls, s):
        return cls(**json.loads(s, object_hook=uuid_parser))
