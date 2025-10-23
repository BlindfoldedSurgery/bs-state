import pytest
import uvloop
from bs_config import Env


@pytest.fixture(scope="session")
def env() -> Env:
    return Env.load(include_default_dotenv=True)


@pytest.fixture(scope="session")
def event_loop_policy():
    return uvloop.EventLoopPolicy()
