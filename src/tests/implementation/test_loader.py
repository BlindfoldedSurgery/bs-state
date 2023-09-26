import pytest
from pydantic import BaseModel

from bs_state import load_state_storage


class StubModel(BaseModel):
    key: str = "value"


@pytest.mark.asyncio
async def test_load_unknown():
    with pytest.raises(ValueError, match="abcdefg"):
        await load_state_storage("abcdefg", StubModel())
