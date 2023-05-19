from collections.abc import Iterator
from typing import Type
from unittest.mock import patch

from dataclasses_avroschema.avrodantic import AvroBaseModel
from kafkit.registry.manager._pydantic import CachedSchema
from kafkit.registry.sansio import MockRegistryApi, RegistryApi


class MockPydanticSchemaManager:
    """A mock PydanticSchemaManager for testing."""

    def __init__(self, registry_api: RegistryApi, suffix: str = "") -> None:
        self._registry = registry_api
        self._models: dict[str, CachedSchema] = {}
        self._suffix = suffix

    async def register_models(
        self,
        models: list[Type[AvroBaseModel]],
        compatibility: str | None = None,
    ) -> None:
        """Register models into the mock's cache."""
        for model in models:
            await self.register_model(model, compatibility=compatibility)

    async def register_model(
        self, model: Type[AvroBaseModel], compatibility: str | None = None
    ) -> None:
        """Register a model into the mock's cache."""
        self._models[model.__name__] = self._cache_model(model)

    def _cache_model(
        self, model: AvroBaseModel | Type[AvroBaseModel]
    ) -> CachedSchema:
        schema_fqn = self._get_model_fqn(model)
        avro_schema = model.avro_schema_to_python()

        if isinstance(model, AvroBaseModel):
            model_type = model.__class__
        else:
            model_type = model

        self._models[schema_fqn] = CachedSchema(
            schema=avro_schema, model=model_type
        )

        return self._models[schema_fqn]

    def _get_model_fqn(
        self, model: AvroBaseModel | Type[AvroBaseModel]
    ) -> str:
        # Mypy can't detect the Meta class on the model, so we have to ignore
        # those lines.

        try:
            name = model.Meta.schema_name  # type: ignore
        except AttributeError:
            name = model.__class__.__name__

        try:
            namespace = model.Meta.namespace  # type: ignore
        except AttributeError:
            namespace = None

        if namespace:
            name = f"{namespace}.{name}"

        if self._suffix:
            name += self._suffix

        return name


def patch_schema_manager() -> Iterator[MockPydanticSchemaManager]:
    """Replace PydanticSchemaManager with a mock."""
    registry = MockRegistryApi(url="http://localhost:8081")
    mock_manager = MockPydanticSchemaManager(registry_api=registry)
    with patch(
        "kafkit.registry.manager.PydanticSchemaManager",
        return_value=mock_manager,
    ):
        yield mock_manager
