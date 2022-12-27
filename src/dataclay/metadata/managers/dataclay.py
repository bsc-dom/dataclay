import json
import uuid

from dataclay.exceptions.exceptions import *
from dataclay.protos import common_messages_pb2
from dataclay.protos.common_messages_pb2 import LANG_NONE
from dataclay.utils.json import UUIDEncoder, uuid_parser


class Backend:
    def __init__(self, id, hostname, port, sl_name, language, dataclay_id):
        self.id = id
        self.hostname = hostname
        self.port = port
        self.sl_name = sl_name
        self.language = language
        self.dataclay_id = dataclay_id

    def key(self):
        return f"/backend/{self.id}"

    def value(self):
        return json.dumps(self.__dict__, cls=UUIDEncoder)

    @classmethod
    def from_json(cls, s):
        return cls(**json.loads(s, object_hook=uuid_parser))

    @classmethod
    def from_proto(cls, proto):
        exe_env = cls(
            uuid.UUID(proto.id),
            proto.hostname,
            proto.port,
            proto.sl_name,
            proto.language,
            uuid.UUID(proto.dataclay_id),
        )
        return exe_env

    # TODO: Improve it with __getattributes__ and interface
    def get_proto(self):
        return common_messages_pb2.Backend(
            id=str(self.id),
            hostname=self.hostname,
            port=self.port,
            sl_name=self.sl_name,
            language=self.language,
            dataclay_id=str(self.dataclay_id),
        )


class StorageLocation:
    def __init__(self, name, hostname, port):
        self.name = name
        self.hostname = hostname
        self.port = port

    def key(self):
        return f"/storagelocation/{self.name}"

    def value(self):
        return json.dumps(self.__dict__, cls=UUIDEncoder)

    @classmethod
    def from_json(cls, s):
        return cls(**json.loads(s, object_hook=uuid_parser))


class Dataclay:
    def __init__(self, id, hostname, port, is_this):
        # TODO: Create new uuid if id is none
        self.id = id
        self.hostname = hostname
        self.port = port
        self.is_this = is_this

    def key(self):
        if self.is_this:
            return "/dataclay/this"
        else:
            return f"/dataclay/{self.id}"

    def value(self):
        return json.dumps(self.__dict__, cls=UUIDEncoder)

    @classmethod
    def from_json(cls, s):
        return cls(**json.loads(s, object_hook=uuid_parser))


class DataclayManager:

    lock = "lock_dataclay"

    def __init__(self, etcd_client):
        self.etcd_client = etcd_client

    def put_ee(self, exec_env):
        """Put exec_env to etcd"""
        self.etcd_client.put(exec_env.key(), exec_env.value())

    def put_dataclay(self, dataclay):
        """Put dataclay to etcd"""
        self.etcd_client.put(dataclay.key(), dataclay.value())

    def get_all_execution_environments(self, lang=None):
        """Get all execution environments"""

        prefix = "/backend/"
        values = self.etcd_client.get_prefix(prefix)
        exec_envs = dict()
        for value, metadata in values:
            key = metadata.key.decode().split("/")[-1]
            exec_env = Backend.from_json(value)
            if lang is None or lang == LANG_NONE or exec_env.language == lang:
                exec_envs[uuid.UUID(key)] = exec_env
        return exec_envs

    def get_dataclay(self, dataclay_id):
        key = f"/dataclay/{dataclay_id}"
        value = self.etcd_client.get(key)[0]
        if value is None:
            raise DataclayDoesNotExistError(dataclay_id)
        return Dataclay.from_json(value)

    def get_dataclay_id(self):
        key = "/this"
        value = self.etcd_client.get(key)[0]
        if value is None:
            raise DataclayDoesNotExistError("this")
        return uuid.UUID(value.decode())

    def put_dataclay_id(self, dataclay_id):
        self.etcd_client.put("/this", str(dataclay_id))

    def get_storage_location(self, sl_name):
        key = f"/storagelocation/{sl_name}"
        value = self.etcd_client.get(key)[0]
        if value is None:
            raise StorageLocationDoesNotExistError(sl_name)
        return StorageLocation.from_json(value)

    def exists_ee(self, id):
        """Returns true if the execution environment exists"""

        key = f"/backend/{id}"
        value = self.etcd_client.get(key)[0]
        return value is not None

    def exists_dataclay(self, id):
        """Returns true if the dataclay exists"""

        key = f"/dataclay/{id}"
        value = self.etcd_client.get(key)[0]
        return value is not None

    def new_execution_environment(self, exe_env: Backend):
        """Creates a new execution environment. Checks that it doesn't exists"""

        with self.etcd_client.lock(self.lock):
            if self.exists_ee(exe_env.id):
                raise ExecutionEnvironmentAlreadyExistError(exe_env.id)
            self.put_ee(exe_env)

    def new_dataclay(self, dataclay: Dataclay):
        """Creates a new dataclay. Checks that it doesn't exists"""

        with self.etcd_client.lock(self.lock):
            if self.exists_dataclay(dataclay.id):
                raise DataclayAlreadyExistError(dataclay.id)
            self.put_dataclay(dataclay)
