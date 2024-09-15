from asyncio import Lock
from importlib.util import find_spec
from typing import Any, Generic, Self, TypeVar

from kubernetes_asyncio.client import ApiException, V1ConfigMap, V1ObjectMeta
from pydantic import BaseModel

from bs_state import AccessException, MissingStateException, StateStorage

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
    DATA_KEY = "state"

    def __init__(
        self,
        state_type: type[T],
        *,
        namespace: str,
        config_map_name: str,
    ) -> None:
        self._type: type[T] = state_type
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
            await storage._create_config_map()
            await storage.store(initial_state)
        return storage

    @property
    def _metadata(self) -> V1ObjectMeta:
        return V1ObjectMeta(
            namespace=self._namespace,
            name=self._config_map_name,
        )

    async def _create_config_map(self) -> None:
        async with client.ApiClient() as api:
            v1 = client.CoreV1Api(api)
            async with self._lock:
                try:
                    await v1.create_namespaced_config_map(
                        namespace=self._namespace,
                        body=V1ConfigMap(
                            metadata=self._metadata,
                            data={},
                        ),
                    )
                except ApiException as e:
                    raise AccessException from e

    async def store(self, state: T) -> None:
        config_map = client.V1ConfigMap(
            metadata=self._metadata,
            data={self.DATA_KEY: state.model_dump_json()},
        )
        async with client.ApiClient() as api:
            v1 = client.CoreV1Api(api)
            async with self._lock:
                try:
                    await v1.replace_namespaced_config_map(
                        name=self._config_map_name,
                        namespace=self._namespace,
                        body=config_map,
                    )
                except ApiException as e:
                    raise AccessException from e

    async def load(self) -> T:
        async with client.ApiClient() as api:
            v1 = client.CoreV1Api(api)
            async with self._lock:
                try:
                    config_map = await v1.read_namespaced_config_map(
                        name=self._config_map_name,
                        namespace=self._namespace,
                    )
                except ApiException as e:
                    if e.status == 404:
                        raise MissingStateException()
                    raise AccessException from e

        data = config_map.data.get(self.DATA_KEY)

        if not data:
            raise MissingStateException()

        return self._type.model_validate_json(data)
