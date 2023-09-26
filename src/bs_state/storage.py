import abc
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class StorageException(Exception):
    pass


class AccessException(StorageException):
    pass


class MissingStateException(StorageException):
    pass


class StateStorage(abc.ABC, Generic[T]):
    @abc.abstractmethod
    async def store(self, state: T) -> None:
        pass

    @abc.abstractmethod
    async def load(self) -> T:
        pass
