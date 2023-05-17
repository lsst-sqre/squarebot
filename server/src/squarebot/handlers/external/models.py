"""Models for the app's external API endpoints."""

from __future__ import annotations

from pydantic import AnyHttpUrl, BaseModel, Field
from safir.metadata import Metadata as SafirMetadata

from rubinobs.square.squarebot.models.slack import SlackUrlVerificationEvent

__all__ = ["IndexResponse", "UrlVerificationResponse"]


class IndexResponse(BaseModel):
    """Metadata returned by the external root URL of the application."""

    metadata: SafirMetadata = Field(..., title="Package metadata")

    api_docs: AnyHttpUrl = Field(..., tile="API documentation URL")


class EventResponse(BaseModel):
    """A response model to a Slack event request."""


class UrlVerificationResponse(BaseModel):
    """A response to a Slack URL verification challenge."""

    challenge: str = Field(
        ...,
        title="Challenge",
        description="Challenge context from the requests 'challenge' field",
    )

    @classmethod
    def from_event(
        cls, request_data: SlackUrlVerificationEvent
    ) -> UrlVerificationResponse:
        return cls(challenge=request_data.challenge)
