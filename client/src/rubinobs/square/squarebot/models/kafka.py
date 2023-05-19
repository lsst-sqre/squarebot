"""Models for Kafka messages produced by Squarebot."""

from __future__ import annotations

import json
from typing import Any, Self

from dataclasses_avroschema.avrodantic import AvroBaseModel
from pydantic import Field

from .slack import SlackChannelType, SlackMessageEvent, SlackMessageType

__all__ = [
    "SquarebotSlackMessageKey",
    "SquarebotSlackMessageValue",
    "SquarebotSlackAppMentionValue",
]


class SquarebotSlackMessageKey(AvroBaseModel):
    """Kafka message key model for Slack messages sent by Squarebot."""

    channel: str = Field(..., description="The Slack channel ID.")

    class Meta:
        """Metadata for the model."""

        namespace = "lsst.square-events.squarebot.messages"
        schema_name = "key"

    @classmethod
    def from_event(cls, event: SlackMessageEvent) -> Self:
        """Create a Kafka key for a Slack message from a Slack event.

        Parameters
        ----------
        event
            The Slack event.

        Returns
        -------
        key
            The Squarebot message key.
        """
        return cls(channel=event.event.channel)


class SquarebotSlackMessageValue(AvroBaseModel):
    """Kafka message value model for Slack messages sent by Squarebot.

    This value schema should be paired with `SquarebotSlackMessageKey` for
    the key schema.
    """

    type: SlackMessageType = Field(..., description="The Slack event type.")

    channel: str = Field(..., description="The Slack channel ID.")

    channel_type: SlackChannelType = Field(
        ..., description="The Slack channel type."
    )

    user: str = Field(
        ..., description="The ID of the user that sent the message."
    )

    ts: str = Field(
        ...,
        description=(
            "The Slack message timestamp. This is string-formatted to allow "
            "comparison with other Slack messges which use the ``ts`` to "
            "identify and reference messages."
        ),
    )

    text: str = Field(..., description="The Slack message text content.")

    slack_event: str = Field(
        ..., description="The original Slack event JSON string."
    )

    class Meta:
        """Metadata for the model."""

        namespace = "lsst.square-events.squarebot.messages"
        schema_name = "value"

    @classmethod
    def from_event(cls, event: SlackMessageEvent, raw: dict[str, Any]) -> Self:
        """Create a Kafka value for a Slack message from a Slack event.

        Parameters
        ----------
        event
            The Slack event.
        raw
            The raw Slack event JSON.

        Returns
        -------
        value
            The Squarebot message value.
        """
        return cls(
            type=event.event.type,
            channel=event.event.channel,
            channel_type=event.event.channel_type,
            user=event.event.user,
            ts=event.event.ts,
            text=event.event.text,
            slack_event=json.dumps(raw),
        )


class SquarebotSlackAppMentionValue(AvroBaseModel):
    """Kafka message value model for Slack app_mention message sent by
    Squarebot.

    These are like `SquarebotSlackMessageValue` but lack a `channel_type`
    field.

    This value schema should be paired with `SquarebotSlackMessageKey` for
    the key schema.
    """

    type: SlackMessageType = Field(..., description="The Slack event type.")

    channel: str = Field(..., description="The Slack channel ID.")

    user: str = Field(
        ..., description="The ID of the user that sent the message."
    )

    ts: str = Field(
        ...,
        description=(
            "The Slack message timestamp. This is string-formatted to allow "
            "comparison with other Slack messges which use the ``ts`` to "
            "identify and reference messages."
        ),
    )

    text: str = Field(..., description="The Slack message text content.")

    slack_event: str = Field(
        ..., description="The original Slack event JSON string."
    )

    class Meta:
        """Metadata for the model."""

        namespace = "lsst.square-events.squarebot.appmention"
        schema_name = "value"

    @classmethod
    def from_event(cls, event: SlackMessageEvent, raw: dict[str, Any]) -> Self:
        """Create a Kafka value for a Slack message from a Slack event.

        Parameters
        ----------
        event
            The Slack event.
        raw
            The raw Slack event JSON.

        Returns
        -------
        value
            The Squarebot message value.
        """
        return cls(
            type=event.event.type,
            channel=event.event.channel,
            channel_type=event.event.channel_type,
            user=event.event.user,
            ts=event.event.ts,
            text=event.event.text,
            slack_event=json.dumps(raw),
        )
