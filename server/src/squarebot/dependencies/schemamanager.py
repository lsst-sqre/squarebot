"""A FastAPI dependency that provides a Kafkit PydanticSchemaManager
for serializing Pydantic models into Avro.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Type

from dataclasses_avroschema.avrodantic import AvroBaseModel
from kafkit.registry.httpx import RegistryApi
from kafkit.registry.manager import PydanticSchemaManager

__all__ = [
    "pydantic_schema_manager_dependency",
    "PydanticSchemaManagerDependency",
]


class PydanticSchemaManagerDependency:
    """A FastAPI dependency that provides a Kafkit PydanticSchemaManager
    for serializing Pydantic models into Avro.
    """

    def __init__(self) -> None:
        self._schema_manager: PydanticSchemaManager | None = None

    async def initialize(
        self,
        *,
        registry_api: RegistryApi,
        models: Iterable[Type[AvroBaseModel]],
        suffix: str = "",
        compatibility: str = "FORWARD",
    ) -> None:
        self._schema_manager = PydanticSchemaManager(
            registry=registry_api, suffix=suffix
        )

        await self._schema_manager.register_models(
            models, compatibility=compatibility
        )

    async def __call__(self) -> PydanticSchemaManager:
        """Get the dependency (call during FastAPI request handling)."""
        if self._schema_manager is None:
            raise RuntimeError("Dependency not initialized")
        return self._schema_manager


pydantic_schema_manager_dependency = PydanticSchemaManagerDependency()