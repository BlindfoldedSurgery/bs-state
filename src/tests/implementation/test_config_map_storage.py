import subprocess
from typing import Any, cast

import pytest
import yaml

from bs_state import StateStorage
from bs_state.implementation import config_map_storage
from tests.implementation.conftest import ImplementationTest, T


@pytest.mark.kubernetes
class TestConfigMapState(ImplementationTest):
    @pytest.fixture
    def kubeconfig(self) -> dict[str, Any]:
        process = subprocess.run(
            args=["kubectl", "config", "view"],
            capture_output=True,
        )

        if (exit_code := process.returncode) != 0:
            raise OSError(f"kubectl config view return code {exit_code}")

        return cast(dict[str, Any], yaml.safe_load(process.stdout))

    @pytest.fixture
    def storage_factory(self, kubeconfig, request):
        async def _factory(state: T) -> StateStorage[T]:
            return await config_map_storage.load(
                initial_state=state,
                namespace="default",
                config_map_name=request.node.name,
            )

        return _factory
