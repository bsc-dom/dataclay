import redis
from dataclay.exceptions.exceptions import *


class KVManager:
    def __init__(self, kv_client: redis.Redis):
        self.r_client = kv_client

    def set_new(self, kv_object):
        """Creates a new dataset. Checks that the dataset doesn't exists."""

        if not self.r_client.set(kv_object.key, kv_object.value, nx=True):
            raise AlreadyExistError(kv_object.key)

    def get_kv(self, kv_class, id):
        """Get kv_class"""

        name = kv_class.path + id
        value = self.r_client.get(name)
        if value is None:
            raise DoesNotExistError(name)

        return kv_class.from_json(value)
