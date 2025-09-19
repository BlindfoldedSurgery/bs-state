from asyncio.locks import Lock
from pathlib import Path
from typing import Self

from opentelemetry import trace
from pydantic import BaseModel

from bs_state import AccessException, MissingStateException, StateStorage

try:
    import aiofile
except ImportError:
    raise RuntimeError("Requires extra 'file', i.e. bs-state[file]")

_tracer = trace.get_tracer(__name__)


@_tracer.start_as_current_span("load")
async def load[T: BaseModel](*, initial_state: T, file: Path) -> StateStorage[T]:
    return await _FileStateStorage.initialize(initial_state, file)


class _FileStateStorage[T: BaseModel](StateStorage[T]):
    def __init__(self, state_type: type[T], file: Path) -> None:
        self._type: type[T] = state_type
        self._file = file
        self._lock = Lock()

    @classmethod
    async def initialize(cls, initial_state: T, file: Path) -> Self:
        storage = cls(type(initial_state), file)
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
                async with aiofile.async_open(self._file, "w") as file:
                    await file.write(json)
            except OSError as e:
                raise AccessException from e

    @_tracer.start_as_current_span("load")
    async def load(self) -> T:
        model = self._type
        async with self._lock:
            try:
                async with aiofile.async_open(self._file, "rb") as file:
                    return model.model_validate_json(await file.read())
            except FileNotFoundError:
                raise MissingStateException(f"No such state file: {self._file}")
            except OSError as e:
                raise AccessException from e
