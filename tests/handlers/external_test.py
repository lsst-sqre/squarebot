"""Tests for the example.handlers.external module and routes."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from httpx import AsyncClient

from squarebot.config import config

from ..support.slackrequester import SlackServer


@pytest.mark.asyncio
async def test_get_index(client: AsyncClient) -> None:
    """Test ``GET /squarebot/``"""
    response = await client.get(f"{config.path_prefix}/")
    assert response.status_code == 200
    data = response.json()
    metadata = data["metadata"]
    assert metadata["name"] == config.name
    assert isinstance(metadata["version"], str)
    assert isinstance(metadata["description"], str)
    assert isinstance(metadata["repository_url"], str)
    assert isinstance(metadata["documentation_url"], str)
    assert data["api_docs"].endswith(f"{config.path_prefix}/redoc")


@pytest.mark.asyncio
async def test_post_event_app_mention(
    client: AsyncClient, sample_slack_message_dir: Path
) -> None:
    """Test ``POST /event`` with an ``app_mention`` payload (happy path)."""
    app_mention_payload = json.loads(
        sample_slack_message_dir.joinpath("app_mention.json").read_text()
    )
    slack_server = SlackServer(client)
    response = await slack_server.post(
        f"{config.path_prefix}/event", json_data=app_mention_payload
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_post_event_missing_timestamp(
    client: AsyncClient, sample_slack_message_dir: Path
) -> None:
    """Test ``POST /event`` with an ``app_mention`` payload where the timestamp
    is missing.
    """
    app_mention_payload = json.loads(
        sample_slack_message_dir.joinpath("app_mention.json").read_text()
    )
    slack_server = SlackServer(client)
    response = await slack_server.post(
        f"{config.path_prefix}/event",
        json_data=app_mention_payload,
        timestamped=False,
    )
    assert response.status_code == 400
    assert response.json()["detail"]["msg"] == (
        "X-Slack-Request-Timestamp header is missing."
    )


@pytest.mark.asyncio
async def test_post_event_bad_timestamp(
    client: AsyncClient, sample_slack_message_dir: Path
) -> None:
    """Test ``POST /event`` with an ``app_mention`` payload where the timestamp
    is incorrect.
    """
    app_mention_payload = json.loads(
        sample_slack_message_dir.joinpath("app_mention.json").read_text()
    )
    slack_server = SlackServer(client)
    response = await slack_server.post(
        f"{config.path_prefix}/event",
        json_data=app_mention_payload,
        bad_timestamp=True,
    )
    assert response.status_code == 400
    assert response.json()["detail"]["msg"] == (
        "X-Slack-Request-Timestamp is older than 5 minutes."
    )


@pytest.mark.asyncio
async def test_post_event_missing_signature(
    client: AsyncClient, sample_slack_message_dir: Path
) -> None:
    """Test ``POST /event`` with an ``app_mention`` payload where the signature
    is missing.
    """
    app_mention_payload = json.loads(
        sample_slack_message_dir.joinpath("app_mention.json").read_text()
    )
    slack_server = SlackServer(client)
    response = await slack_server.post(
        f"{config.path_prefix}/event",
        json_data=app_mention_payload,
        signed=False,
    )
    assert response.status_code == 400
    assert response.json()["detail"]["msg"] == (
        "Could not successfully verify X-Slack-Signature"
    )


@pytest.mark.asyncio
async def test_post_event_wrong_signature(
    client: AsyncClient, sample_slack_message_dir: Path
) -> None:
    """Test ``POST /event`` with an ``app_mention`` payload where the signature
    is incorrect.
    """
    app_mention_payload = json.loads(
        sample_slack_message_dir.joinpath("app_mention.json").read_text()
    )
    slack_server = SlackServer(client)
    response = await slack_server.post(
        f"{config.path_prefix}/event",
        json_data=app_mention_payload,
        bad_signature=True,
    )
    assert response.status_code == 400
    assert response.json()["detail"]["msg"] == (
        "Could not successfully verify X-Slack-Signature"
    )
