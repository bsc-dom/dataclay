from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Optional

import redis.asyncio as redis
from redis.exceptions import ConnectionError, RedisClusterException

from dataclay.exceptions import AlreadyExistError, DoesNotExistError

if TYPE_CHECKING:
    from uuid import UUID

    from dataclay.metadata.kvdata import KeyValue

logger = logging.getLogger(__name__)


class RedisManager:
    def __init__(self, host: str, port: int = 6379):
        self._client = redis.Redis(host=host, port=port)

        # TODO: This won't work since the cluster is not initialized
        # and the exception is not caught. We could use _client.initialize()
        # but it's not async and can't be called from __init__
        # try:
        #     self._client = redis.RedisCluster(host=host, port=port)
        #     self._client.initialize()
        # except (RedisClusterException, IndexError):
        #     logger.warning("Redis cluster not found, using single node")
        #     self._client = redis.Redis(host=host, port=port)

    # @classmethod
    # async def initialize(cls, host: str, port: int = 6379):
    #     self = cls(host=host, port=port)
    #     try:
    #         logger.warning("trying to cluster")
    #         self._client = redis.RedisCluster(host=host, port=port)
    #         await self._client.initialize()
    #         logger.warning("Redis cluster found")
    #     except (RedisClusterException, IndexError):
    #         logger.warning("Redis cluster not found, using single node")
    #         self._client = redis.Redis(host=host, port=port)
    #         await self._client.initialize()
    #     return self

    async def close(self):
        await self._client.close()

    # Need for generic pubsub interface, so we can use it in the same way as etcd
    def publish(self, channel: str, message: str):
        """Publishes a message to a channel"""
        return self._client.publish(channel, message)

    # TODO: Create a better interface for pubsub
    def pubsub(self):
        """Returns a pubsub object"""
        return self._client.pubsub()

    async def is_ready(self, timeout: Optional[float] = None, pause: float = 0.5):
        ref = time.time()
        now = ref
        while timeout is None or (now - ref) < timeout:
            try:
                return await self._client.ping()
            except ConnectionError:
                time.sleep(pause)
                now = time.time()
        return False

    async def set_new(self, kv_object: KeyValue):
        """Sets a new key, failing if already exists.

        Use "set" if the key is using a UUID (should avoid conflict),
        in order to optimize for etcd (if used)
        """
        if not await self._client.set(kv_object.key, kv_object.value, nx=True):
            raise AlreadyExistError(kv_object.key)

    async def set(self, kv_object: KeyValue):
        """Sets a key, overwriting if already exists."""
        await self._client.set(kv_object.key, kv_object.value)

    async def update(self, kv_object: KeyValue):
        """Updates a key that already exists.

        It could be used "set(..)" instead, but "update" makes sure the key was not deleted
        """
        if not await self._client.set(kv_object.key, kv_object.value, xx=True):
            raise DoesNotExistError(kv_object.key)

    async def get_kv(self, kv_class: KeyValue, id: str | UUID):
        """Get kv_class"""

        name = kv_class.path + str(id)
        value = await self._client.get(name)
        if value is None:
            raise DoesNotExistError(name)

        return kv_class.from_json(value)

    async def getdel_kv(self, kv_class: KeyValue, id: str | UUID):
        """Get kv_class and delete key"""

        name = kv_class.path + str(id)
        value = await self._client.getdel(name)
        if value is None:
            raise DoesNotExistError(name)

        return kv_class.from_json(value)

    async def delete_kv(self, *names: str):
        """Delete one or more keys"""
        await self._client.delete(*names)

    async def getprefix(self, kv_class: KeyValue, prefix: str) -> dict[str, KeyValue]:
        """Get a dict for all kv with prefix"""
        result = {}
        async for key in self._client.scan_iter(prefix + "*"):
            value = await self._client.get(key)
            value = kv_class.from_json(value)
            result[key.decode().removeprefix(prefix)] = value
        return result

    async def lock(self, name: str):
        return await self._client.lock("/lock" + name)
