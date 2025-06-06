import abc

from pydantic import BaseModel


class StorageException(Exception):
    pass


class AccessException(StorageException):
    pass


class MissingStateException(StorageException):
    pass


class StateStorage[T: BaseModel](abc.ABC):
    @abc.abstractmethod
    async def store(self, state: T) -> None:
        pass

    @abc.abstractmethod
    async def load(self) -> T:
        pass
