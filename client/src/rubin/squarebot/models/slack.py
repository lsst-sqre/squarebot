"""Slack API models."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

__all__ = [
    "SlackPlainTextObject",
    "SlackMrkdwnTextObject",
    "BaseSlackEvent",
    "SlackBlockActionBase",
    "SlackBlockActionsMessage",
    "SlackBlockActionsMessageAttachmentContainer",
    "SlackBlockActionsMessageContainer",
    "SlackBlockActionsPayload",
    "SlackBlockActionsViewContainer",
    "SlackChannel",
    "SlackChannelType",
    "SlackMessageAttachment",
    "SlackMessageAttachmentField",
    "SlackMessageEvent",
    "SlackMessageEventContent",
    "SlackMessageSubtype",
    "SlackMessageType",
    "SlackStaticSelectAction",
    "SlackStaticSelectActionSelectedOption",
    "SlackTeam",
    "SlackUrlVerificationEvent",
    "SlackUser",
]


# SlackPlainTextObject and SlackMrkdwnTextObject are composition objects
# that should belong to a Safir Block Kit models library. They are included
# here for the interim.


class SlackPlainTextObject(BaseModel):
    """A plain_text composition object.

    https://api.slack.com/reference/block-kit/composition-objects#text
    """

    type: Literal["plain_text"] = Field(
        "plain_text", description="The type of object."
    )

    text: str = Field(..., description="The text to display.")

    emoji: bool = Field(
        True,
        description=(
            "Indicates whether emojis in text should be escaped into colon "
            "emoji format."
        ),
    )


class SlackMrkdwnTextObject(BaseModel):
    """A mrkdwn text composition object.

    https://api.slack.com/reference/block-kit/composition-objects#text
    """

    type: Literal["mrkdwn"] = Field(
        "mrkdwn", description="The type of object."
    )

    text: str = Field(..., description="The text to display.")

    verbatim: bool = Field(
        False,
        description=(
            "Indicates whether the text should be treated as verbatim. When "
            "`True`, URLs will not be auto-converted into links and "
            "channel names will not be auto-converted into links."
        ),
    )


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
    """An enumeration of the different types of Slack messages."""

    app_mention = "app_mention"
    """A message that mentions the app."""

    message = "message"
    """A regular message."""


class SlackChannelType(str, Enum):
    """Represents the type of a Slack channel."""

    channel = "channel"
    """A public channel."""

    group = "group"
    """A private channel."""

    im = "im"
    """A direct message."""

    mpim = "mpim"
    """A multi-person direct message."""


class SlackMessageSubtype(str, Enum):
    """Represents the subtype of a Slack message.

    See https://api.slack.com/events/message#subtypes
    """

    bot_message = "bot_message"
    """A message sent by an integration."""


class SlackMessageAttachmentField(BaseModel):
    """A model for a field in a Slack message attachment.

    See https://api.slack.com/reference/messaging/attachments#field_objects
    """

    title: str | None = Field(
        None,
        description=(
            "The title of the field. This is not markdown-formatted, but it "
            "can contain some limited formatting."
        ),
    )

    value: str | None = Field(
        None,
        description=(
            "The value of the field. This is not markdown-formatted, but it "
            "can contain some limited formatting."
        ),
    )

    short: bool | None = Field(
        None,
        description=(
            "Whether the field is short enough to be displayed next to other "
            "fields. This is a hint to the Slack client."
        ),
    )

    @property
    def combined_text_content(self) -> str:
        """The combined text content of the field."""
        if self.title and self.value:
            return f"{self.title}: {self.value}"
        elif self.title:
            return self.title
        elif self.value:
            return self.value
        else:
            return ""


class SlackMessageAttachment(BaseModel):
    """A model for individual Slack message attachments.

    Attachments are an old-style way to add structured content to messages,
    but is still popular with my app integrations.
    """

    text: str | None = Field(
        None,
        description=(
            "The text content of the field as mrkdwn. `text` in attachments "
            "deprecated, with a preference for fields instead."
        ),
    )

    fields: list[SlackMessageAttachmentField] | None = Field(
        None, description=("An array of fields to display in the attachment.")
    )

    @property
    def combined_text_content(self) -> str:
        """The combined text content of the attachment."""
        combined_text = self.text or ""
        if self.fields:
            combined_text += "\n\n".join(
                field.combined_text_content for field in self.fields
            )
        return combined_text


class SlackMessageEventContent(BaseModel):
    """A model for the ``event`` field inside a message event.

    See https://api.slack.com/events/app_mention,
    https://api.slack.com/events/message, and
    https://api.slack.com/events/message/bot_message
    """

    type: SlackMessageType = Field(description="The Slack message type.")

    subtype: SlackMessageSubtype | None = Field(
        None, description="The message subtype."
    )

    channel: str = Field(
        description=(
            "ID of the channel where the message was sent "
            "(e.g., C0LAN2Q65)."
        )
    )

    channel_type: SlackChannelType | None = Field(
        description=(
            "The type of channel (public, direct im, etc..). This is null for "
            "``app_mention`` events."
        )
    )

    user: str | None = Field(
        None,
        description=(
            "The ID of the user that sent the message (eg U061F7AUR). "
            "This is null for bot messages."
        ),
    )

    text: str = Field(description="Content of the message.")

    ts: str = Field(description="Timestamp of the message.")

    event_ts: str = Field(description="When the event was dispatched.")

    thread_ts: str | None = Field(
        None,
        description=(
            "The timestamp of the parent message. This is only present in "
            "threaded messages."
        ),
    )

    bot_id: str | None = Field(
        None,
        description=(
            "The unique identifier of the bot user that sent the message. "
            "This field is only present if the message was sent by a bot."
        ),
    )

    attachments: list[SlackMessageAttachment] | None = Field(
        None,
        description=(
            "An array of attachments that were included in the message."
        ),
    )

    @property
    def combined_text_content(self) -> str:
        """The combined text content of the message and its attachments."""
        combined_text = self.text
        for attachment in self.attachments or []:
            combined_text += f"\n\n{attachment.text}"
        return combined_text


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

    authed_users: list[str] | None = Field(
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


class SlackBlockActionsMessageContainer(BaseModel):
    """A model for the container field in Slack interaction payloads triggered
    by block actions in a message.
    """

    type: Literal["message"] = Field(
        description="The type of container.",
    )

    message_ts: str = Field(description="The timestamp of the message.")

    channel_id: str = Field(description="The ID of the channel.")

    is_ephemeral: bool = Field(description="Whether the message is ephemeral.")


class SlackBlockActionsMessageAttachmentContainer(BaseModel):
    """A model for the container field in Slack interaction payloads triggered
    by a block message attachment.
    """

    type: Literal["message_attachment"] = Field(
        description="The type of container.",
    )

    message_ts: str = Field(description="The timestamp of the message.")

    channel_id: str = Field(description="The ID of the channel.")

    is_ephemeral: bool = Field(description="Whether the message is ephemeral.")

    is_app_unfurl: bool = Field(
        description="Whether the message is an app unfurl."
    )


class SlackBlockActionsViewContainer(BaseModel):
    """A model for the container field in Slack interaction payloads triggered
    by a block action view.
    """

    type: Literal["view"] = Field(
        description="The type of container.",
    )

    view_id: str = Field(description="The ID of the view.")


class SlackBlockActionsMessage(BaseModel):
    """A model for the message field in Slack interaction payloads."""

    type: Literal["message"] = Field(description="The type of container.")

    ts: str = Field(..., description="The timestamp of the message.")

    thread_ts: str | None = Field(
        None,
        description=(
            "The timestamp of the parent message. This is only present in "
            "threaded messages."
        ),
    )

    user: str | None = Field(
        None,
        description=("The ID of the user or bot that sent the message."),
    )

    bot_id: str | None = Field(
        None,
        description=(
            "The ID of the Slack App integration that sent the message. This "
            "is null for non-bot messages."
        ),
    )


class SlackBlockActionBase(BaseModel):
    """A base model for a Slack block action."""

    type: str = Field(description="The type of action.")

    action_id: str = Field(description="The action ID.")

    block_id: str = Field(description="The block ID.")

    action_ts: str = Field(description="The timestamp of the action.")


class SlackStaticSelectActionSelectedOption(BaseModel):
    """A model for the selected option in a static select action."""

    text: SlackPlainTextObject = Field(
        ...,
        description=(
            "The text of the selected option. This is only present for static "
            "select actions."
        ),
    )

    value: str = Field(description="The value of the selected option.")


class SlackStaticSelectAction(SlackBlockActionBase):
    """A model for a static select action in a Slack block."""

    type: Literal["static_select"] = Field(description="The type of action.")

    selected_option: SlackStaticSelectActionSelectedOption = Field(
        ...,
        description=(
            "The selected option. This is only present for static select "
            "actions."
        ),
    )


class SlackBlockActionsPayload(BaseModel):
    """A model for a Slack Block kit interaction.

    This isn't yet a full model for a block actions payload; experience is
    needed to fully understand what the payloads are for the types of
    interactions we use.

    See https://api.slack.com/reference/interaction-payloads/block-actions
    """

    type: Literal["block_actions"] = Field(
        description="Interaction payload type."
    )

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

    user: SlackUser = Field(
        description=(
            "Information about the user that triggered the interaction."
        )
    )

    team: SlackTeam | None = Field(
        description=(
            "Information about the Slack team. Null for org-installed apps."
        )
    )

    channel: SlackChannel | None = Field(
        description=(
            "Information about the Slack channel where the interaction "
            "occurred."
        )
    )

    container: (
        SlackBlockActionsMessageContainer
        | SlackBlockActionsMessageAttachmentContainer
        | SlackBlockActionsViewContainer
    ) = Field(description="Container where this interaction occurred.")

    message: SlackBlockActionsMessage | None = Field(
        None, description="The message where the interaction occurred."
    )

    # Add more action types as needed.
    actions: list[SlackStaticSelectAction] = Field(
        description="The actions that were triggered."
    )
