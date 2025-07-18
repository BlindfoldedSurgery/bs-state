import asyncio
from asyncio.locks import Lock
from importlib.util import find_spec
from typing import Self

from pydantic import BaseModel

from bs_state import AccessException, MissingStateException, StateStorage

if find_spec("redis") is None:
    raise RuntimeError("Requires extra 'redis', i.e. bs-state[redis]")

import redis.asyncio as redis
from redis.exceptions import AuthenticationError, RedisError


async def load[T: BaseModel](
    *,
    initial_state: T,
    host: str,
    port: int = 6379,
    username: str | None = None,
    password: str | None = None,
    key: str | None = None,
) -> StateStorage[T]:
    client = redis.Redis(
        host=host,
        port=port,
        password=password,
        username=username,
        protocol=3,
    )
    try:
        await client.ping()
    except AuthenticationError as e:
        asyncio.create_task(client.aclose())
        raise AccessException("Authentication with Redis failed") from e
    except RedisError as e:
        asyncio.create_task(client.aclose())
        raise AccessException("Could not ping Redis") from e

    return await _RedisStateStorage.initialize(initial_state, client, key)


class _RedisStateStorage[T: BaseModel](StateStorage[T]):
    def __init__(self, state_type: type[T], client: redis.Redis, key: str) -> None:
        self._type: type[T] = state_type
        self._client = client
        self._key = key
        self._lock = Lock()

    @classmethod
    async def initialize(
        cls,
        initial_state: T,
        client: redis.Redis,
        key: str | None,
    ) -> Self:
        storage = cls(type(initial_state), client, key or "state")

        try:
            # See if there are values
            await storage.load()
        except MissingStateException:
            await storage.store(initial_state)
        return storage

    async def store(self, state: T) -> None:
        json = state.model_dump_json()
        async with self._lock:
            try:
                await self._client.set(self._key, json)
            except RedisError as e:
                raise AccessException("Could not update value in Redis") from e

    async def load(self) -> T:
        model = self._type
        async with self._lock:
            try:
                result = await self._client.get(self._key)
            except RedisError as e:
                raise AccessException("Could not retrieve value from Redis") from e

            if result is None:
                raise MissingStateException()

            return model.model_validate_json(result)

    async def close(self) -> None:
        async with self._lock:
            await self._client.aclose()
