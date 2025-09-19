import asyncio
from asyncio.locks import Lock
from importlib.util import find_spec
from typing import Self

from opentelemetry import trace
from pydantic import BaseModel

from bs_state import AccessException, MissingStateException, StateStorage

if find_spec("valkey") is None:
    raise RuntimeError("Requires extra 'valkey', i.e. bs-state[valkey]")

import valkey.asyncio as valkey
from opentelemetry.instrumentation.redis import RedisInstrumentor
from valkey.exceptions import AuthenticationError, ValkeyError

_tracer = trace.get_tracer(__name__)


@_tracer.start_as_current_span("load")
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

    RedisInstrumentor().instrument_client(client)  # type: ignore

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
    @_tracer.start_as_current_span("initialize")
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

    @_tracer.start_as_current_span("store")
    async def store(self, state: T) -> None:
        json = state.model_dump_json()
        async with self._lock:
            try:
                await self._client.set(self._key, json)
            except ValkeyError as e:
                raise AccessException("Could not update value in Valkey") from e

    @_tracer.start_as_current_span("load")
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

    @_tracer.start_as_current_span("close")
    async def close(self) -> None:
        async with self._lock:
            await self._client.aclose()
