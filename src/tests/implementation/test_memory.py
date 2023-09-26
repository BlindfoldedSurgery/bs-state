from __future__ import annotations

import pytest_asyncio

from bs_state import StateStorage, load_state_storage
from tests.implementation.conftest import ImplementationTest, StubState


class TestMemory(ImplementationTest):
    @pytest_asyncio.fixture
    async def storage(self, state: StubState) -> StateStorage[StubState]:
        return await load_state_storage("memory", state)
