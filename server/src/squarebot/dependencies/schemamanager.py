"""A FastAPI dependency that provides a Kafkit PydanticSchemaManager
for serializing Pydantic models into Avro.
"""

from collections.abc import Iterable
from typing import Type

from dataclasses_avroschema.avrodantic import AvroBaseModel
from httpx import AsyncClient
from kafkit.registry import manager  # this is patched in tests
from kafkit.registry.httpx import RegistryApi

__all__ = [
    "pydantic_schema_manager_dependency",
    "PydanticSchemaManagerDependency",
]


class PydanticSchemaManagerDependency:
    """A FastAPI dependency that provides a Kafkit PydanticSchemaManager
    for serializing Pydantic models into Avro.
    """

    def __init__(self) -> None:
        self._schema_manager: manager.PydanticSchemaManager | None = None

    async def initialize(
        self,
        *,
        http_client: AsyncClient,
        registry_url: str,
        models: Iterable[Type[AvroBaseModel]],
        suffix: str = "",
        compatibility: str = "FORWARD",
    ) -> None:
        registry_api = RegistryApi(http_client=http_client, url=registry_url)
        self._schema_manager = manager.PydanticSchemaManager(
            registry=registry_api, suffix=suffix
        )

        await self._schema_manager.register_models(
            models, compatibility=compatibility
        )

    async def __call__(self) -> manager.PydanticSchemaManager:
        """Get the dependency (call during FastAPI request handling)."""
        if self._schema_manager is None:
            raise RuntimeError("Dependency not initialized")
        return self._schema_manager


pydantic_schema_manager_dependency = PydanticSchemaManagerDependency()
