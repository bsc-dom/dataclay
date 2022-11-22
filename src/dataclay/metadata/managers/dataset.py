import json
import uuid

from opentelemetry import trace

from dataclay_common.exceptions.exceptions import *
from dataclay_common.utils.json import UUIDEncoder, uuid_parser

tracer = trace.get_tracer(__name__)


class Dataset:
    def __init__(self, name, owner, is_public=False):
        """
        Args:
            name: Name of the dataset.
            owner: Username of the dataset owner.
            is_public: If dataset has public access.
        """
        self.name = name
        self.owner = owner
        self.is_public = is_public

    def key(self):
        return f"/dataset/{self.name}"

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
