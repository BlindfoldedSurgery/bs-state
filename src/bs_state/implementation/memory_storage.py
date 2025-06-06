from typing import Any, Self

from pydantic import BaseModel

from bs_state import StateStorage


async def load[T: BaseModel](*, initial_state: T) -> StateStorage[T]:
    return _MemoryStateStorage.initialize(initial_state)


class _MemoryStateStorage[T: BaseModel](StateStorage[T]):
    def __init__(self, initial_state: T) -> None:
        self._type: type[T] = type(initial_state)
        self._values: dict[str, Any] = initial_state.model_dump()

    @classmethod
    def initialize(cls, initial_state: T) -> Self:
        return cls(initial_state)

    async def store(self, state: T) -> None:
        self._values = state.model_dump()

    async def load(self) -> T:
        return self._type.model_validate(self._values)
