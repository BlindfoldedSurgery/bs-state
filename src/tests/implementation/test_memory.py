from __future__ import annotations

import pytest
import pytest_asyncio
from pydantic import BaseModel

from bs_state import StateStorage, load_state_storage


class StubState(BaseModel):
    string: str
    integer: int
    double: float
    array: list[str]
    heterogeneous_collection: tuple[str, int, float]
    map: dict[str, str]
    sub_model: StubState | None


@pytest.fixture
def state() -> StubState:
    return StubState(
        string="test",
        integer=42,
        double=1.234,
        array=["a", "b", "c"],
        heterogeneous_collection=("a", 42, 1.234),
        map={"a": "b"},
        sub_model=StubState(
            string="test2",
            integer=43,
            double=2.345,
            array=["d", "e", "f"],
            heterogeneous_collection=("b", 43, 2.345),
            map={"c": "d"},
            sub_model=None,
        ),
    )


@pytest_asyncio.fixture
async def storage(state: StubState) -> StateStorage[StubState]:
    return await load_state_storage("memory", state)


@pytest.mark.asyncio
async def test_load(state):
    storage = await load_state_storage("memory", state)
    assert isinstance(storage, StateStorage)


@pytest.mark.asyncio
async def test_load_copies_state(state):
    storage = await load_state_storage("memory", state)
    state.string = "changed"
    loaded_state = await storage.load()
    assert loaded_state.string == "test"


@pytest.mark.asyncio
async def test_initial_state_matches(
    storage: StateStorage[StubState],
    state: StubState,
) -> None:
    loaded_state = await storage.load()
    assert isinstance(loaded_state, StubState)
    assert loaded_state == state


@pytest.mark.asyncio
async def test_store_works(storage: StateStorage[StubState], state: StubState) -> None:
    state.string = "changed"
    await storage.store(state)
    loaded = await storage.load()
    assert loaded.string == "changed"
    assert loaded == state
