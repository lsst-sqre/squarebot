"""Tests for the Slack service (separate from the API endpoints)."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest
from _pytest.logging import LogCaptureFixture
from safir.logging import LogLevel, Profile, configure_logging
from structlog import get_logger

from squarebot.config import config
from squarebot.services.kafkaproducer import PydanticKafkaProducer
from squarebot.services.slack import SlackService


@pytest.mark.asyncio
async def test_publish_event_app_mention(
    mock_kafka_producer: PydanticKafkaProducer,
    caplog: LogCaptureFixture,
    sample_slack_message_dir: Path,
) -> None:
    """Test processing an ``app_mention`` event.

    Use logging capture as a proxy for testing Kafka publication in the future.
    """
    caplog.set_level(logging.DEBUG, logger="squarebot")
    configure_logging(
        name="squarebot", profile=Profile.production, log_level=LogLevel.DEBUG
    )
    logger = get_logger("squarebot")

    # kafka_producer = AIOKafkaProducer(
    #     bootstrap_servers=config.kafka_bootstrap_servers,
    # )
    # registry_api = RegistryApi(
    #     http_client=http_client, registry_url=config.registry_url
    # )
    slack = SlackService(logger=logger, config=config)

    app_mention_payload = json.loads(
        sample_slack_message_dir.joinpath("app_mention.json").read_text()
    )
    await slack.publish_event(app_mention_payload)

    last_message = json.loads(caplog.record_tuples[-1][-1])
    assert last_message["event"] == "Got a Slack message"
    assert last_message["event_type"] == "app_mention"


@pytest.mark.asyncio
async def test_publish_event_message_channels(
    caplog: LogCaptureFixture,
    sample_slack_message_dir: Path,
) -> None:
    """Test processing a ``message.channels`` event.

    Use logging capture as a proxy for testing Kafka publication in the future.
    """
    caplog.set_level(logging.DEBUG, logger="squarebot")
    configure_logging(
        name="squarebot", profile=Profile.production, log_level=LogLevel.DEBUG
    )
    logger = get_logger("squarebot")

    slack = SlackService(logger=logger, config=config)

    app_mention_payload = json.loads(
        sample_slack_message_dir.joinpath("message.channels.json").read_text()
    )
    await slack.publish_event(app_mention_payload)

    last_message = json.loads(caplog.record_tuples[-1][-1])
    assert last_message["event"] == "Got a Slack message"
    assert last_message["event_type"] == "message"
    assert last_message["channel_type"] == "channel"


@pytest.mark.asyncio
async def test_publish_event_message_groups(
    caplog: LogCaptureFixture,
    sample_slack_message_dir: Path,
) -> None:
    """Test processing a ``message.groups`` event.

    Use logging capture as a proxy for testing Kafka publication in the future.
    """
    caplog.set_level(logging.DEBUG, logger="squarebot")
    configure_logging(
        name="squarebot", profile=Profile.production, log_level=LogLevel.DEBUG
    )
    logger = get_logger("squarebot")

    slack = SlackService(logger=logger, config=config)

    app_mention_payload = json.loads(
        sample_slack_message_dir.joinpath("message.groups.json").read_text()
    )
    await slack.publish_event(app_mention_payload)

    last_message = json.loads(caplog.record_tuples[-1][-1])
    assert last_message["event"] == "Got a Slack message"
    assert last_message["event_type"] == "message"
    assert last_message["channel_type"] == "group"


@pytest.mark.asyncio
async def test_publish_event_message_mpim(
    caplog: LogCaptureFixture,
    sample_slack_message_dir: Path,
) -> None:
    """Test processing a ``message.mpim`` event.

    Use logging capture as a proxy for testing Kafka publication in the future.
    """
    caplog.set_level(logging.DEBUG, logger="squarebot")
    configure_logging(
        name="squarebot", profile=Profile.production, log_level=LogLevel.DEBUG
    )
    logger = get_logger("squarebot")

    slack = SlackService(logger=logger, config=config)

    app_mention_payload = json.loads(
        sample_slack_message_dir.joinpath("message.mpim.json").read_text()
    )
    await slack.publish_event(app_mention_payload)

    last_message = json.loads(caplog.record_tuples[-1][-1])
    assert last_message["event"] == "Got a Slack message"
    assert last_message["event_type"] == "message"
    assert last_message["channel_type"] == "mpim"


@pytest.mark.asyncio
async def test_publish_event_message_im(
    caplog: LogCaptureFixture,
    sample_slack_message_dir: Path,
) -> None:
    """Test processing a ``message.im`` event.

    Use logging capture as a proxy for testing Kafka publication in the future.
    """
    caplog.set_level(logging.DEBUG, logger="squarebot")
    configure_logging(
        name="squarebot", profile=Profile.production, log_level=LogLevel.DEBUG
    )
    logger = get_logger("squarebot")

    slack = SlackService(logger=logger, config=config)

    app_mention_payload = json.loads(
        sample_slack_message_dir.joinpath("message.im.json").read_text()
    )
    await slack.publish_event(app_mention_payload)

    last_message = json.loads(caplog.record_tuples[-1][-1])
    assert last_message["event"] == "Got a Slack message"
    assert last_message["event_type"] == "message"
    assert last_message["channel_type"] == "im"
