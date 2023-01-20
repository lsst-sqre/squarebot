"""Slack API models."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

__all__ = [
    "BaseSlackEvent",
    "SlackUrlVerificationEvent",
    "SlackMessageEvent",
    "SlackMessageType",
    "SlackChannelType",
    "SlackMessageEventContent",
    "SlackBlockAction",
    "SlackUser",
    "SlackTeam",
    "SlackChannel",
]


class BaseSlackEvent(BaseModel):
    """A model for the minimal request payload from Slack for an event.

    Any event message is gauranteed to have these fields. For specific types of
    events, re-parse the request body with a specific model such as
    `SlackMessageEvent`. For information about all the Slack event types, see
    https://api.slack.com/events.
    """

    type: str = Field(
        ...,
        description=(
            "The Slack event type in the message's outer scope; typically "
            "this is ``url_verification`` or ``event_callback``."
        ),
    )


class SlackUrlVerificationEvent(BaseSlackEvent):
    """A Slack ``url_verification`` event."""

    challenge: str = Field(..., description="URL challenge content.")


class SlackMessageType(str, Enum):

    app_mention = "app_mention"
    message = "message"


class SlackChannelType(str, Enum):

    channel = "channel"  # public channel
    group = "group"  # private channel
    im = "im"  # direct message
    mpim = "mpim"  # multi-persion direct message


class SlackMessageEventContent(BaseModel):
    """A model for the ``event`` field inside a message event.

    See https://api.slack.com/events/app_mention and
    https://api.slack.com/events/message.
    """

    type: SlackMessageType = Field(description="The Slack message type.")

    channel: str = Field(
        description=(
            "ID of the channel where the message was sent "
            "(e.g., C0LAN2Q65)."
        )
    )

    channel_type: SlackChannelType = Field(
        description="The type of channel (public, direct im, etc..)"
    )

    user: str = Field(
        description="The ID of the user that sent the message (eg U061F7AUR)."
    )

    text: str = Field(description="Content of the message.")

    ts: str = Field(description="Timestamp of the message.")

    event_ts: str = Field(description="When the event was dispatched.")


class SlackMessageEvent(BaseSlackEvent):
    """A Slack event for message events in general.

    See https://api.slack.com/events/app_mention and
    https://api.slack.com/events/message.
    """

    team_id: str = Field(
        description=(
            "The unique identifier of the workspace where the event occurred."
        )
    )

    api_app_id: str = Field(
        description=(
            "The unique identifier of your installed Slack application. Use "
            "this to distinguish which app the event belongs to if you use "
            "multiple apps with the same Request URL."
        )
    )

    event_id: str = Field(
        description=(
            "A unique identifier for this specific event, globally unique "
            "across all workspaces."
        )
    )

    event_time: int = Field(
        description=(
            "The epoch timestamp in seconds indicating when this event was "
            "dispatched."
        )
    )

    authed_users: Optional[list[str]] = Field(
        None,
        description=(
            "An array of string-based User IDs. Each member of the collection "
            "represents a user that has installed your application/bot and "
            "indicates the described event would be visible to those users."
        ),
    )

    event: SlackMessageEventContent


class SlackUser(BaseModel):
    """A model for the user field in Slack interaction payloads."""

    id: str = Field(description="ID of the user.")

    username: str = Field(description="User name of the user.")

    team_id: str = Field(description="The user's team.")


class SlackTeam(BaseModel):
    """A model for the team field in Slack interaction payloads."""

    id: str = Field(description="ID of the team.")

    domain: str = Field(description="Domain name of the team.")


class SlackChannel(BaseModel):
    """A model for the channel field in Slack interaction payloads."""

    id: str = Field(description="ID of the channel.")

    name: str = Field(description="Name of the channel.")


class SlackBlockAction(BaseModel):
    """A model for a Slack Block kit interaction.

    This isn't yet a full model for a block action payload; experience is
    needed to fully understand what the payloads are for the types of
    interactions we use.

    See https://api.slack.com/reference/interaction-payloads/block-actions
    """

    type: str = Field(description="Should be `block_actions`.")

    trigger_id: str = Field(
        description="A short-lived ID used to launch modals."
    )

    api_app_id: str = Field(
        description=(
            "The unique identifier of your installed Slack application. Use "
            "this to distinguish which app the event belongs to if you use "
            "multiple apps with the same Request URL."
        )
    )

    response_url: str = Field(
        description=(
            "A short-lived URL to send message in response to interactions."
        )
    )

    user: SlackUser = Field(
        description=(
            "Information about the user that triggered the interaction."
        )
    )

    team: SlackTeam = Field(description="Information about the Slack team.")

    channel: SlackChannel = Field(
        description="Information about the Slack channel."
    )
