import json
import uuid

from opentelemetry import trace

from dataclay.exceptions.exceptions import *
from dataclay.utils.json import UUIDEncoder, uuid_parser

from dataclasses import dataclass

tracer = trace.get_tracer(__name__)


from abc import ABC, abstractmethod


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


class DatasetManager:

    lock = "lock_dataset"

    def __init__(self, etcd_client):
        self.etcd_client = etcd_client

    @tracer.start_as_current_span("put_dataset")
    def put_dataset(self, dataset):
        # Store dataset in etcd
        self.etcd_client.put(dataset.key(), dataset.value())

    @tracer.start_as_current_span("get_dataset")
    def get_dataset(self, dataset_name):
        # Get dataset from etcd and checks that it exists
        key = f"/dataset/{dataset_name}"
        value = self.etcd_client.get(key)[0]
        if value is None:
            raise DatasetDoesNotExistError(dataset_name)

        return Dataset.from_json(value)

    @tracer.start_as_current_span("exists_dataset")
    def exists_dataset(self, dataset_name):
        """ "Returns true if dataset exists"""

        key = f"/dataset/{dataset_name}"
        value = self.etcd_client.get(key)[0]
        return value is not None

    @tracer.start_as_current_span("new_dataset")
    def new_dataset(self, dataset):
        """Creates a new dataset. Checks that the dataset doesn't exists."""

        with self.etcd_client.lock(self.lock):
            if self.exists_dataset(dataset.name):
                raise DatasetAlreadyExistError(dataset.name)
            self.put_dataset(dataset)
