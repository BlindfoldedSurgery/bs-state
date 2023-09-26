import importlib
from typing import Type, TypeVar

from pydantic import BaseModel

from bs_state.storage import StateStorage

T = TypeVar("T", bound=BaseModel)


async def load_state_storage(name: str, initial_state: T) -> StateStorage[T]:
    try:
        module = importlib.import_module(f"bs_state.implementation.{name}")
    except ImportError:
        raise ValueError(f"Unknown StateStorage implementation: {name}")

    storage_class: Type[StateStorage[T]] = getattr(
        module,
        f"{name.capitalize()}StateStorage",
    )

    return await storage_class.initialize(initial_state)
