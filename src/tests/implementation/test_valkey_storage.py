from dataclasses import dataclass
from typing import Self

import pytest
from bs_config import Env
from pydantic import BaseModel

from bs_state import StateStorage
from bs_state.implementation import valkey_storage
from tests.implementation.conftest import ImplementationTest


@dataclass(frozen=True)
class ValkeyConfig:
    host: str
    port: int

    @classmethod
    def from_env(cls, env: Env) -> Self:
        return cls(
            host=env.get_string("VALKEY_HOST", default="localhost"),
            port=env.get_int("VALKEY_PORT", default=6369),
        )


@pytest.mark.valkey
class TestRedisState(ImplementationTest):
    @pytest.fixture(scope="class")
    def valkey_config(self, env: Env) -> ValkeyConfig:
        return ValkeyConfig.from_env(env)

    @pytest.fixture
    def storage_factory(self, valkey_config, request):
        async def _factory[T: BaseModel](state: T) -> StateStorage[T]:
            return await valkey_storage.load(
                initial_state=state,
                host=valkey_config.host,
                port=valkey_config.port,
                key=request.node.name,
            )

        return _factory
