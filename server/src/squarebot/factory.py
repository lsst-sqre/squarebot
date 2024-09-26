"""Factory for Squarebot services and other components."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from faststream.kafka import KafkaBroker
from faststream.kafka.asyncapi import Publisher
from structlog.stdlib import BoundLogger

from .config import config
from .kafkarouter import kafka_router
from .services.slack import SlackService


@dataclass(kw_only=True, frozen=True, slots=True)
class ProcessContext:
    """Holds singletons in the context of a Ook process, which might be a
    API server or a CLI command.
    """

    kafka_broker: KafkaBroker
    """The aiokafka broker provided through the FastStream Kafka router."""

    channel_publisher: Publisher
    """A Kafka publisher for the message channels topic."""

    im_publisher: Publisher
    """A Kafka publisher for the Slack IM channels topic."""

    mpim_publisher: Publisher
    """A Kafka publisher for the Slack multi-person IM channels topic."""

    groups_publisher: Publisher
    """A Kafka publisher for the Slack private channels topic."""

    app_mentions_publisher: Publisher
    """A Kafka publisher for the Slack ``app_mention`` topic."""

    block_actions_publisher: Publisher
    """A Kafka publisher for the Slack block actions topic."""

    view_submission_publisher: Publisher
    """A Kafka publisher for the Slack view submissions topic."""

    @classmethod
    async def create(cls) -> Self:
        broker = kafka_router.broker
        return cls(
            kafka_broker=broker,
            channel_publisher=broker.publisher(
                config.message_channels_topic,
                description="Slack public channel messages.",
            ),
            im_publisher=broker.publisher(
                config.message_im_topic, description="Slack IM messages."
            ),
            mpim_publisher=broker.publisher(
                config.message_mpim_topic, description="Slack MPIM messages."
            ),
            groups_publisher=broker.publisher(
                config.message_groups_topic,
                description="Slack private-channel messages.",
            ),
            app_mentions_publisher=broker.publisher(
                config.app_mention_topic,
                description="Slack bot mention messages.",
            ),
            block_actions_publisher=broker.publisher(
                config.block_actions_topic,
                description="Slack block actions.",
            ),
            view_submission_publisher=broker.publisher(
                config.view_submission_topic,
                description="Slack view submission.",
            ),
        )

    async def aclose(self) -> None:
        """Close any resources held by the context."""


class Factory:
    """Factory for Squarebot services and other components."""

    def __init__(
        self,
        *,
        logger: BoundLogger,
        process_context: ProcessContext,
    ) -> None:
        self._process_context = process_context
        self._logger = logger

    def create_slack_service(self) -> SlackService:
        """Create a Slack service."""
        return SlackService(
            logger=self._logger,
            config=config,
            app_mentions_publisher=self._process_context.app_mentions_publisher,
            channel_publisher=self._process_context.channel_publisher,
            im_publisher=self._process_context.im_publisher,
            mpim_publisher=self._process_context.mpim_publisher,
            groups_publisher=self._process_context.groups_publisher,
            block_actions_publisher=self._process_context.block_actions_publisher,
            view_submission_publisher=self._process_context.view_submission_publisher,
        )
