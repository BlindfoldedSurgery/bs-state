from typing import Any, Generic, Self, Type, TypeVar

from pydantic import BaseModel

from bs_state import StateStorage

T = TypeVar("T", bound=BaseModel)


async def load(*, initial_state: T) -> StateStorage[T]:
    return _MemoryStateStorage.initialize(initial_state)


class _MemoryStateStorage(StateStorage[T], Generic[T]):
    def __init__(self, initial_state: T) -> None:
        self._type: Type[T] = type(initial_state)
        self._values: dict[str, Any] = initial_state.model_dump()

    @classmethod
    def initialize(cls, initial_state: T) -> Self:
        return cls(initial_state)

    async def store(self, state: T) -> None:
        self._values = state.model_dump()

    async def load(self) -> T:
        return self._type.model_validate(self._values)
