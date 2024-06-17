import json
import logging
from abc import ABC, abstractmethod
from typing import Annotated, ClassVar, Optional, Union
from uuid import UUID, uuid4

import bcrypt
<<<<<<< HEAD
from google.protobuf.json_format import MessageToDict
from pydantic import BaseModel, BeforeValidator, Field
=======
from google.protobuf.json_format import MessageToDict, ParseDict
from pydantic import BaseModel, Field
>>>>>>> 09cda3b (relaxing, downgrading requirements and fixing. Rebased onto main)

from dataclay.proto.common import common_pb2

logger = logging.getLogger(__name__)


class KeyValue(BaseModel, ABC):
    @property
    @abstractmethod
    def key(self):
        pass

    @property
    def value(self):
        return self.json()

    @property
    @abstractmethod
    def path(self):
        pass

    @property
    @abstractmethod
    def proto_class(self):
        pass

    @classmethod
    def from_json(cls, s):
        return cls.parse_raw(s)

    @classmethod
    def from_proto(cls, proto):
        return cls.parse_obj(MessageToDict(proto, preserving_proto_field_name=True))

    def get_proto(self):
        # Converting to json and back to dict to ensure UUID are bytes (and not UUID instances)
        return self.proto_class(**json.loads(self.json()))


class Dataclay(KeyValue):
    path: ClassVar = "/dataclay/"
    proto_class: ClassVar = common_pb2.Dataclay

    id: UUID
    host: str
    port: int
    is_this: bool = False

    @property
    def key(self):
        return self.path + ("this" if self.is_this else str(id))


class Backend(KeyValue):
    path: ClassVar = "/backend/"
    proto_class: ClassVar = common_pb2.Backend

    id: UUID
    host: str
    port: int
    dataclay_id: UUID

    @property
    def key(self):
        return self.path + str(self.id)


class ObjectMetadata(KeyValue):
    path: ClassVar = "/object/"
    proto_class: ClassVar = common_pb2.ObjectMetadata

    id: UUID = Field(default_factory=uuid4)
    dataset_name: Optional[str] = None
    class_name: str
    master_backend_id: Optional[UUID] = None
    replica_backend_ids: set[UUID] = Field(default_factory=set)
    is_read_only: bool = False
    original_object_id: Optional[UUID] = None
    versions_object_ids: list[UUID] = Field(default_factory=list)

    @property
    def key(self):
        return self.path + str(self.id)


class Alias(KeyValue):
    path: ClassVar = "/alias/"
    proto_class: ClassVar = common_pb2.Alias

    name: str
    dataset_name: str
    object_id: UUID

    @property
    def key(self):
        return self.path + f"{self.dataset_name}/{self.name}"


class Account(KeyValue):
    path: ClassVar = "/account/"
    proto_class: ClassVar = None

    username: str
    hashed_password: Optional[str] = None
    role: str = "NORMAL"
    datasets: list = Field(default_factory=list)

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
    proto_class: ClassVar = None

    name: str
    owner: str
    is_public: bool = False

    @property
    def key(self):
        return self.path + self.name
