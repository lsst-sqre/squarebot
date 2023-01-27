"""Handlers for the app's external root, ``/squarebot/``."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Form, Request, Response
from safir.metadata import get_metadata

from squarebot.config import config
from squarebot.dependencies.requestcontext import (
    RequestContext,
    context_dependency,
)
from squarebot.domain.slack import BaseSlackEvent, SlackUrlVerificationEvent

from .models import IndexResponse, UrlVerificationResponse

__all__ = ["external_router", "get_index"]

external_router = APIRouter()
"""FastAPI router for all external handlers."""


@external_router.get(
    "/",
    response_model=IndexResponse,
    response_model_exclude_none=True,
    summary="Application metadata",
)
async def get_index(
    request: Request,
) -> IndexResponse:
    """GET metadata about the application."""
    metadata = get_metadata(
        package_name="squarebot",
        application_name=config.name,
    )
    # Construct these URLs; this doesn't use request.url_for because the
    # endpoints are in other FastAPI "apps".
    doc_url = request.url.replace(path=f"/{config.path_prefix}/redoc")
    return IndexResponse(metadata=metadata, api_docs=str(doc_url))


@external_router.post(
    "/event", summary="Handle Slack event", response_model=None
)
async def post_event(
    slack_event: BaseSlackEvent,
    context: RequestContext = Depends(context_dependency),
) -> Response | UrlVerificationResponse:
    """Handle an event post by the Slack Events API."""
    # Verify the Slack signing secret on the request
    await context.slack.verify_request(context.request)

    request_json = await context.request.json()
    if slack_event.type == "url_verification":
        return UrlVerificationResponse.from_event(
            SlackUrlVerificationEvent.parse_obj(request_json)
        )
    elif slack_event.type == "event_callback":
        try:
            await context.slack.publish_event(request_json=request_json)
        except Exception:
            context.logger.exception("Unexpectedly failed to process event")
        finally:
            # Always return a 200 so Slack knows we're still listening.
            return Response(status_code=200)
    else:
        context.logger.debug("Slack event type unknown", type=slack_event.type)
        return Response(status_code=200)


@external_router.post("/interaction", summary="Handle Slack interaction")
async def post_interaction(
    payload: str = Form(),
    context: RequestContext = Depends(context_dependency),
) -> Response:
    """Handle an interaction payload from Slack."""
    # Verify the Slack signing secret on the request
    await context.slack.verify_request(context.request)

    interaction_payload = json.loads(payload)

    try:
        await context.slack.publish_interaction(
            interaction_payload=interaction_payload
        )
    except Exception:
        context.logger.exception("Unexpectedly failed to process interaction")
    finally:
        # Always return a 200 so Slack knows we're still listening.
        return Response(status_code=200)
