from dataclasses import dataclass
from typing import Self

import pytest
from bs_config import Env
from pydantic import BaseModel

from bs_state import StateStorage
from bs_state.implementation import redis_storage
from tests.implementation.conftest import ImplementationTest


@dataclass(frozen=True)
class RedisConfig:
    host: str
    port: int

    @classmethod
    def from_env(cls, env: Env) -> Self:
        return cls(
            host=env.get_string("REDIS_HOST", default="localhost"),
            port=env.get_int("REDIS_PORT", default=6379),
        )


@pytest.mark.redis
class TestRedisState(ImplementationTest):
    @pytest.fixture(scope="class")
    def redis_config(self, env: Env) -> RedisConfig:
        return RedisConfig.from_env(env)

    @pytest.fixture
    def storage_factory(self, redis_config, request):
        async def _factory[T: BaseModel](state: T) -> StateStorage[T]:
            return await redis_storage.load(
                initial_state=state,
                host=redis_config.host,
                port=redis_config.port,
                key=request.node.name,
            )

        return _factory
