from pathlib import Path

import pytest
from pydantic import BaseModel

from bs_state import AccessException, StateStorage
from bs_state.implementation import file_storage
from tests.implementation.conftest import ImplementationTest, T


class EmptyState(BaseModel):
    key: str = "value"


class TestFileState(ImplementationTest):
    @pytest.fixture
    def storage_factory(self, tmp_path_factory):
        path = tmp_path_factory.mktemp("file_state")

        async def _factory(state: T) -> StateStorage[T]:
            return await file_storage.load(
                initial_state=state, file=path / "state.json"
            )

        return _factory

    @pytest.mark.parametrize(
        "file",
        ["/proc/1", "/proc/999999"],
    )
    @pytest.mark.asyncio
    async def test_initialize_inaccessible(self, file):
        with pytest.raises(AccessException):
            await file_storage.load(
                initial_state=EmptyState(),
                file=Path(file),
            )
