import abc
from typing import Generic, Self, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class StateStorage(abc.ABC, Generic[T]):
    @classmethod
    @abc.abstractmethod
    async def initialize(cls, initial_state: T) -> Self:
        pass

    @abc.abstractmethod
    async def store(self, state: T) -> None:
        pass

    @abc.abstractmethod
    async def load(self) -> T:
        pass
