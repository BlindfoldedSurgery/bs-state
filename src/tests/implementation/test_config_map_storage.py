import json
import subprocess
from typing import Any, cast

import pytest

from bs_state import StateStorage
from bs_state.implementation import config_map_storage
from tests.implementation.conftest import ImplementationTest, T


@pytest.mark.kubernetes
class TestConfigMapState(ImplementationTest):
    @pytest.fixture
    def kubeconfig(self) -> dict[str, Any]:
        process = subprocess.run(
            args=["kubectl", "config", "view", "-o=json"],
            capture_output=True,
            timeout=3,
        )

        if (exit_code := process.returncode) != 0:
            raise OSError(f"kubectl config view return code {exit_code}")

        result = cast(dict[str, Any], json.loads(process.stdout))
        return result

    @pytest.fixture
    def storage_factory(self, kubeconfig, request):
        async def _factory(state: T) -> StateStorage[T]:
            return await config_map_storage.load(
                initial_state=state,
                namespace="default",
                config_map_name=request.node.name,
                kubeconfig=kubeconfig,
            )

        return _factory
