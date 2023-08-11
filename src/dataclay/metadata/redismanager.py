from __future__ import annotations

import time
from typing import TYPE_CHECKING

import redis

from dataclay.exceptions.exceptions import *

if TYPE_CHECKING:
    from dataclay.metadata.kvdata import KeyValue


class RedisManager:
    def __init__(self, host, port=6379):
        self.r_client = redis.Redis(host=host, port=port)

    def is_ready(self, timeout=None, pause=0.5):
        ref = time.time()
        now = ref
        while timeout is None or (now - ref) < timeout:
            try:
                return self.r_client.ping()
            except redis.ConnectionError:
                time.sleep(pause)
                now = time.time()
        return False

    def set_new(self, kv_object):
        """Creates a new dataset. Checks that the dataset doesn't exists.

        Use "set" if the key is using a UUID, in order to optimize for etcd (if used)
        """

        if not self.r_client.set(kv_object.key, kv_object.value, nx=True):
            raise AlreadyExistError(kv_object.key)

    def set(self, kv_object):
        self.r_client.set(kv_object.key, kv_object.value)

    def update(self, kv_object):
        """Updates a key that already exists.

        It could be used "set(..)" instead, but "update" makes sure the key was not deleted
        """
        if not self.r_client.set(kv_object.key, kv_object.value, xx=True):
            raise DoesNotExistError(kv_object.key)

    def get_kv(self, kv_class: KeyValue, id):
        """Get kv_class"""

        name = kv_class.path + str(id)
        value = self.r_client.get(name)
        if value is None:
            raise DoesNotExistError(name)

        return kv_class.from_json(value)

    def getdel_kv(self, kv_class: KeyValue, id):
        """Get kv_class and delete key"""

        name = kv_class.path + str(id)
        value = self.r_client.getdel(name)
        if value is None:
            raise DoesNotExistError(name)

        return kv_class.from_json(value)

    def delete_kv(self, *names):
        """Delete one or more keys"""
        self.r_client.delete(*names)

    def getprefix(self, kv_class: KeyValue, prefix):
        """Get a dict for all kv with prefix"""
        result = dict()
        for key in self.r_client.scan_iter(prefix + "*"):
            value = self.r_client.get(key)
            value = kv_class.from_json(value)
            result[key.decode().removeprefix(prefix)] = value
        return result

    def lock(self, name):
        return self.r_client.lock("/lock" + name)
