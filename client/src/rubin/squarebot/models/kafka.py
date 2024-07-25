"""Models for Kafka messages produced by Squarebot."""

from __future__ import annotations

import json
from typing import Any, Self

from pydantic import BaseModel, Field

from .slack import (
    SlackChannelType,
    SlackMessageEvent,
    SlackMessageSubtype,
    SlackMessageType,
)

__all__ = [
    "SquarebotSlackMessageKey",
    "SquarebotSlackMessageValue",
    "SquarebotSlackAppMentionValue",
]


class SquarebotSlackMessageKey(BaseModel):
    """Kafka message key model for Slack messages sent by Squarebot."""

    channel: str = Field(..., description="The Slack channel ID.")

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

    def to_key_bytes(self) -> bytes:
        """Serialize the key to bytes for use as a Kafka key.

        Returns
        -------
        bytes
            The serialized key.
        """
        return self.channel.encode("utf-8")


class SquarebotSlackMessageValue(BaseModel):
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
        ...,
        description=(
            "The ID of the user or bot that sent the message. See the "
            "is_bot field to determine if the user is a bot."
        ),
    )

    ts: str = Field(
        ...,
        description=(
            "The Slack message timestamp. This is string-formatted to allow "
            "comparison with other Slack messges which use the ``ts`` to "
            "identify and reference messages."
        ),
    )

    thread_ts: str | None = Field(
        None,
        description=(
            "The timestamp of the parent message. This is only present in "
            "threaded messages."
        ),
    )

    text: str = Field(..., description="The Slack message text content.")

    slack_event: str = Field(
        ..., description="The original Slack event JSON string."
    )

    is_bot: bool = Field(
        False,
        description="Flag that is true if `user` is a bot user ID.",
    )

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
        if event.event.channel_type is None:
            raise ValueError(
                "Cannot create a SquarebotSlackMessageValue from a Slack "
                "event that lacks a channel_type. Is this an app_mention?"
            )

        if (
            event.event.subtype is not None
            and event.event.subtype == SlackMessageSubtype.bot_message
        ):
            is_bot = True
            if event.event.bot_id is None:
                raise ValueError(
                    "Cannot create a SquarebotSlackMessageValue from a Slack "
                    "bot_message event that lacks a bot_id."
                )
            user_id = event.event.bot_id
        else:
            is_bot = False
            if event.event.user is None:
                raise ValueError(
                    "Cannot create a SquarebotSlackMessageValue from a Slack "
                    "message event that lacks a user."
                )
            user_id = event.event.user

        return cls(
            type=event.event.type,
            channel=event.event.channel,
            channel_type=event.event.channel_type,
            user=user_id,
            ts=event.event.ts,
            thread_ts=event.event.thread_ts,
            text=event.event.combined_text_content,
            slack_event=json.dumps(raw),
            is_bot=is_bot,
        )


class SquarebotSlackAppMentionValue(BaseModel):
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
        if event.event.user is None:
            raise ValueError(
                "Cannot create a SquarebotSlackAppMentionValue from a Slack "
                "app_mention event that lacks a user. Is this a bot message?"
            )
        return cls(
            type=event.event.type,
            channel=event.event.channel,
            user=event.event.user,
            ts=event.event.ts,
            text=event.event.text,
            slack_event=json.dumps(raw),
        )
