from asyncio import Lock
from importlib.util import find_spec
from typing import Any, Generic, Self, Type, TypeVar

from pydantic import BaseModel

from bs_state import MissingStateException, StateStorage

if find_spec("kubernetes_asyncio") is None:
    raise RuntimeError("Requires extra 'kubernetes', i.e. bs-state[kubernetes]")

from kubernetes_asyncio import client, config

T = TypeVar("T", bound=BaseModel)


async def load(
    *,
    initial_state: T,
    namespace: str,
    config_map_name: str,
    kubeconfig: dict[str, Any] | None = None,
) -> StateStorage[T]:
    return await _ConfigMapStateStorage.initialize(
        initial_state,
        namespace=namespace,
        config_map_name=config_map_name,
        kubeconfig=kubeconfig,
    )


class _ConfigMapStateStorage(StateStorage[T], Generic[T]):
    def __init__(
        self,
        state_type: Type[T],
        *,
        namespace: str,
        config_map_name: str,
    ) -> None:
        self._type: Type[T] = state_type
        self._namespace = namespace
        self._config_map_name = config_map_name
        self._lock = Lock()

    @classmethod
    async def initialize(
        cls,
        initial_state: T,
        *,
        namespace: str,
        config_map_name: str,
        kubeconfig: dict[str, Any] | None,
    ) -> Self:
        if kubeconfig is None:
            config.load_incluster_config()
        else:
            await config.load_kube_config_from_dict(kubeconfig)

        storage = cls(
            type(initial_state),
            namespace=namespace,
            config_map_name=config_map_name,
        )
        try:
            # See if there are values
            await storage.load()
        except MissingStateException:
            await storage.store(initial_state)
        return storage

    async def store(self, state: T) -> None:
        config_map = client.V1ConfigMap(data=state.model_dump_json())
        async with client.ApiClient() as api:
            v1 = client.CoreV1Api(api)
            async with self._lock:
                await v1.replace_namespaced_config_map(
                    name=self._config_map_name,
                    namespace=self._namespace,
                    body=config_map,
                )

    async def load(self) -> T:
        async with self._lock:
            async with client.ApiClient() as api:
                v1 = client.CoreV1Api(api)
                async with self._lock:
                    config_map = await v1.read_namespaced_config_map(
                        name=self._config_map_name,
                        namespace=self._namespace,
                    )

        return self._type.model_validate(config_map.data)