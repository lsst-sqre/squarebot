"""Tests for the example.handlers.external module and routes."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from aiokafka import AIOKafkaConsumer
from httpx import AsyncClient

from rubin.squarebot.models.kafka import (
    SquarebotSlackAppMentionValue,
    SquarebotSlackMessageValue,
)
from squarebot.config import config

from ..support.slackrequester import SlackServer


async def _create_consumer(topic: str) -> AIOKafkaConsumer:
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=config.kafka.bootstrap_servers,
        group_id="squarebot-test",
    )
    await consumer.start()
    await consumer.seek_to_end()
    return consumer


@pytest.mark.asyncio
async def test_get_index(client: AsyncClient) -> None:
    """Test ``GET /squarebot/``."""
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
    """Test ``POST /slack/event`` with an ``app_mention`` payload
    (happy path).
    """
    consumer = await _create_consumer(config.app_mention_topic)

    slack_payload = json.loads(
        sample_slack_message_dir.joinpath("app_mention.json").read_text()
    )
    slack_server = SlackServer(client)

    response = await slack_server.post(
        f"{config.path_prefix}/slack/event", json_data=slack_payload
    )
    assert response.status_code == 200

    # Verify that the message was sent to the Kafka topic
    message = await consumer.getone()
    value = SquarebotSlackAppMentionValue.model_validate_json(
        message.value.decode("utf-8")
    )
    assert value.text == slack_payload["event"]["text"]
    await consumer.stop()


@pytest.mark.asyncio
async def test_post_event_message_channels(
    client: AsyncClient, sample_slack_message_dir: Path
) -> None:
    """Test ``POST /slack/event`` with a ``message.channels`` payload
    (happy path).
    """
    consumer = await _create_consumer(config.message_channels_topic)

    slack_payload = json.loads(
        sample_slack_message_dir.joinpath("message.channels.json").read_text()
    )
    slack_server = SlackServer(client)
    response = await slack_server.post(
        f"{config.path_prefix}/slack/event", json_data=slack_payload
    )
    assert response.status_code == 200

    # Verify that the message was sent to the Kafka topic
    message = await consumer.getone()
    value = SquarebotSlackMessageValue.model_validate_json(
        message.value.decode("utf-8")
    )
    assert value.text == slack_payload["event"]["text"]
    await consumer.stop()


@pytest.mark.asyncio
async def test_post_event_message_im(
    client: AsyncClient, sample_slack_message_dir: Path
) -> None:
    """Test ``POST /slack/event`` with a ``message.im`` payload
    (happy path).
    """
    consumer = await _create_consumer(config.message_im_topic)

    slack_payload = json.loads(
        sample_slack_message_dir.joinpath("message.im.json").read_text()
    )
    slack_server = SlackServer(client)
    response = await slack_server.post(
        f"{config.path_prefix}/slack/event", json_data=slack_payload
    )
    assert response.status_code == 200

    # Verify that the message was sent to the Kafka topic
    message = await consumer.getone()
    value = SquarebotSlackMessageValue.model_validate_json(
        message.value.decode("utf-8")
    )
    assert value.text == slack_payload["event"]["text"]
    await consumer.stop()


@pytest.mark.asyncio
async def test_post_event_message_groups(
    client: AsyncClient, sample_slack_message_dir: Path
) -> None:
    """Test ``POST /slack/event`` with a ``message.groups`` payload
    (happy path).
    """
    consumer = await _create_consumer(config.message_groups_topic)

    slack_payload = json.loads(
        sample_slack_message_dir.joinpath("message.groups.json").read_text()
    )
    slack_server = SlackServer(client)
    response = await slack_server.post(
        f"{config.path_prefix}/slack/event", json_data=slack_payload
    )
    assert response.status_code == 200

    # Verify that the message was sent to the Kafka topic
    message = await consumer.getone()
    value = SquarebotSlackMessageValue.model_validate_json(
        message.value.decode("utf-8")
    )
    assert value.text == slack_payload["event"]["text"]
    await consumer.stop()


@pytest.mark.asyncio
async def test_post_event_message_mpim(
    client: AsyncClient, sample_slack_message_dir: Path
) -> None:
    """Test ``POST /slack/event`` with a ``message.mpim`` payload
    (happy path).
    """
    consumer = await _create_consumer(config.message_mpim_topic)

    slack_payload = json.loads(
        sample_slack_message_dir.joinpath("message.mpim.json").read_text()
    )
    slack_server = SlackServer(client)
    response = await slack_server.post(
        f"{config.path_prefix}/slack/event", json_data=slack_payload
    )
    assert response.status_code == 200

    # Verify that the message was sent to the Kafka topic
    message = await consumer.getone()
    value = SquarebotSlackMessageValue.model_validate_json(
        message.value.decode("utf-8")
    )
    assert value.text == slack_payload["event"]["text"]
    await consumer.stop()


@pytest.mark.asyncio
async def test_post_bot_message(
    client: AsyncClient, sample_slack_message_dir: Path
) -> None:
    """Test ``POST /slack/event`` with a bot_message payload subtype
    (happy path).
    """
    consumer = await _create_consumer(config.message_groups_topic)

    slack_payload = json.loads(
        sample_slack_message_dir.joinpath("bot_message.json").read_text()
    )
    slack_server = SlackServer(client)
    response = await slack_server.post(
        f"{config.path_prefix}/slack/event", json_data=slack_payload
    )
    assert response.status_code == 200

    # Verify that the message was sent to the Kafka topic
    message = await consumer.getone()
    value = SquarebotSlackMessageValue.model_validate_json(
        message.value.decode("utf-8")
    )
    # Check that we're getting the combined text that includes attachments
    assert "Lorem ipsum" in value.text
    await consumer.stop()


@pytest.mark.asyncio
async def test_post_event_missing_timestamp(
    client: AsyncClient, sample_slack_message_dir: Path
) -> None:
    """Test ``POST /slack/event`` with an ``app_mention`` payload where the
    timestamp is missing.
    """
    app_mention_payload = json.loads(
        sample_slack_message_dir.joinpath("app_mention.json").read_text()
    )
    slack_server = SlackServer(client)
    response = await slack_server.post(
        f"{config.path_prefix}/slack/event",
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
    """Test ``POST /slack/event`` with an ``app_mention`` payload where the
    timestamp is incorrect.
    """
    app_mention_payload = json.loads(
        sample_slack_message_dir.joinpath("app_mention.json").read_text()
    )
    slack_server = SlackServer(client)
    response = await slack_server.post(
        f"{config.path_prefix}/slack/event",
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
    """Test ``POST /slack/event`` with an ``app_mention`` payload where the
    signature is missing.
    """
    app_mention_payload = json.loads(
        sample_slack_message_dir.joinpath("app_mention.json").read_text()
    )
    slack_server = SlackServer(client)
    response = await slack_server.post(
        f"{config.path_prefix}/slack/event",
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
    """Test ``POST /slack/event`` with an ``app_mention`` payload where the
    signature is incorrect.
    """
    app_mention_payload = json.loads(
        sample_slack_message_dir.joinpath("app_mention.json").read_text()
    )
    slack_server = SlackServer(client)
    response = await slack_server.post(
        f"{config.path_prefix}/slack/event",
        json_data=app_mention_payload,
        bad_signature=True,
    )
    assert response.status_code == 400
    assert response.json()["detail"]["msg"] == (
        "Could not successfully verify X-Slack-Signature"
    )
