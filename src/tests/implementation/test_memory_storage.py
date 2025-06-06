import pytest
from pydantic import BaseModel

from bs_state import StateStorage
from bs_state.implementation import memory_storage
from tests.implementation.conftest import ImplementationTest


class TestMemoryState(ImplementationTest):
    @pytest.fixture
    def storage_factory(self):
        async def _factory[T: BaseModel](state: T) -> StateStorage[T]:
            return await memory_storage.load(initial_state=state)

        return _factory
