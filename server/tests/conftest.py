"""Test fixtures for squarebot tests."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from unittest.mock import Mock

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient

from squarebot import main

from .support.kafkaproducer import patch_aiokafkaproducer
from .support.schemamanager import (
    MockPydanticSchemaManager,
    patch_schema_manager,
)


@pytest.fixture
def mock_schema_manager() -> Iterator[MockPydanticSchemaManager]:
    """Return a mock PydanticSchemaManager for testing."""
    yield from patch_schema_manager()


@pytest.fixture
def mock_kafka_producer() -> Iterator[Mock]:
    """Return a mock KafkaProducer for testing."""
    yield from patch_aiokafkaproducer()


@pytest_asyncio.fixture
async def app(
    mock_kafka_producer: Mock,
    mock_schema_manager: MockPydanticSchemaManager,
) -> AsyncIterator[FastAPI]:
    """Return a configured test application.

    Wraps the application in a lifespan manager so that startup and shutdown
    events are sent during test execution.
    """
    async with LifespanManager(main.app):
        yield main.app


@pytest_asyncio.fixture
async def http_client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient() as client:
        yield client


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Return an ``httpx.AsyncClient`` configured to talk to the test app."""
    async with AsyncClient(app=app, base_url="https://example.com/") as client:
        yield client


@pytest.fixture
def sample_slack_message_dir() -> Path:
    """Return the directory for the sample Slack message datasets."""
    return Path(__file__).parent.joinpath("slack_messages")
