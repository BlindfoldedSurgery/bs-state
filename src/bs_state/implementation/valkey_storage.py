import asyncio
from asyncio.locks import Lock
from importlib.util import find_spec
from typing import Self

from pydantic import BaseModel

from bs_state import AccessException, MissingStateException, StateStorage

if find_spec("valkey") is None:
    raise RuntimeError("Requires extra 'valkey', i.e. bs-state[valkey]")

import valkey.asyncio as valkey
from valkey.exceptions import AuthenticationError, ValkeyError


async def load[T: BaseModel](
    *,
    initial_state: T,
    host: str,
    port: int = 6379,
    username: str | None = None,
    password: str | None = None,
    key: str | None = None,
) -> StateStorage[T]:
    client = valkey.Valkey(
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
        raise AccessException("Authentication with Valkey failed") from e
    except ValkeyError as e:
        asyncio.create_task(client.aclose())
        raise AccessException("Could not ping Valkey") from e

    return await _ValkeyStateStorage.initialize(initial_state, client, key)


class _ValkeyStateStorage[T: BaseModel](StateStorage[T]):
    def __init__(self, state_type: type[T], client: valkey.Valkey, key: str) -> None:
        self._type: type[T] = state_type
        self._client = client
        self._key = key
        self._lock = Lock()

    @classmethod
    async def initialize(
        cls,
        initial_state: T,
        client: valkey.Valkey,
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
            except ValkeyError as e:
                raise AccessException("Could not update value in Valkey") from e

    async def load(self) -> T:
        model = self._type
        async with self._lock:
            try:
                result = await self._client.get(self._key)
            except ValkeyError as e:
                raise AccessException("Could not retrieve value from Valkey") from e

            if result is None:
                raise MissingStateException()

            return model.model_validate_json(result)

    async def close(self) -> None:
        async with self._lock:
            await self._client.aclose()
