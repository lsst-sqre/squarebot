"""Slack service layer."""

from __future__ import annotations

import hashlib
import hmac
import math
import time
from typing import Any

from fastapi import HTTPException, Request, status
from faststream.kafka.asyncapi import Publisher
from structlog.stdlib import BoundLogger

from rubin.squarebot.models.kafka import (
    SquarebotSlackAppMentionValue,
    SquarebotSlackMessageKey,
    SquarebotSlackMessageValue,
)
from rubin.squarebot.models.slack import (
    SlackBlockActionsPayload,
    SlackChannelType,
    SlackMessageEvent,
    SlackMessageType,
)

from ..config import Configuration


class SlackService:
    """A service for processing with Slack messages and interactions."""

    def __init__(
        self,
        logger: BoundLogger,
        config: Configuration,
        app_mentions_publisher: Publisher,
        channel_publisher: Publisher,
        groups_publisher: Publisher,
        im_publisher: Publisher,
        mpim_publisher: Publisher,
    ) -> None:
        self._logger = logger
        self._config = config
        self._app_mentions_publisher = app_mentions_publisher
        self._channel_publisher = channel_publisher
        self._groups_publisher = groups_publisher
        self._im_publisher = im_publisher
        self._mpim_publisher = mpim_publisher

    @staticmethod
    def compute_slack_signature(
        signing_secret: str, body: str, timestamp: str
    ) -> str:
        """Compute the hash of the message, which can be compared to the
        ``X-Slack-Signature`` header.

        See: https://api.slack.com/docs/verifying-requests-from-slack

        Parameters
        ----------
        signing_secret
            The app's Slack signing secret.
        body
            The request body content.
        timestamp
            The timestamp (the ``X-Slack-Request-Timestamp``).

        Returns
        -------
        signature_digest
            The SHA 256 hex digest of the signature, matching
            ``X-Slack-Signature``.
        """
        base_signature = f"v0:{timestamp}:{body}"
        return (
            "v0="
            + hmac.new(
                signing_secret.encode(),
                msg=base_signature.encode(),
                digestmod=hashlib.sha256,
            ).hexdigest()
        )

    async def verify_request(self, request: Request) -> bool:
        """Verify that the request came from Slack using the signing sercret
        method.


        See: https://api.slack.com/docs/verifying-requests-from-slack

        Parameters
        ----------
        request
            The request object.

        Returns
        -------
        bool
            Returns `True` if the request is valid. An `HTTPException` is
            raised for invalid requests.

        Raises
        ------
        fastapi.HTTPException
            Raised for requests that cannot be validated.
        """
        try:
            timestamp = request.headers["X-Slack-Request-Timestamp"]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "msg": ("X-Slack-Request-Timestamp header is missing."),
                    "type": "bad_request",
                },
            ) from None

        if math.fabs(time.time() - float(timestamp)) > 300.0:
            # The request timestamp is more than five minutes from local time.
            # It could be a replay attack, so let's ignore it.
            self._logger.warning(
                "X-Slack-Request-Timestamp is older than 5 minutes."
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "msg": (
                        "X-Slack-Request-Timestamp is older than 5 minutes."
                    ),
                    "type": "bad_request",
                },
            )

        # Ensure that no special decoding is done on the body
        body_bytes = await request.body()
        body = body_bytes.decode(encoding="utf-8")

        # Compute the hash of the message and compare it ot X-Slack-Signature
        signing_secret = self._config.slack_signing_secret.get_secret_value()
        signature_hash = SlackService.compute_slack_signature(
            signing_secret, body, timestamp
        )
        if hmac.compare_digest(
            signature_hash, request.headers.get("X-Slack-Signature", "")
        ):
            return True
        else:
            self._logger.warning(
                "Could not successfully verify X-Slack-Signature"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "msg": "Could not successfully verify X-Slack-Signature",
                    "type": "bad_request",
                },
            )

    async def publish_event(self, request_json: dict[str, Any]) -> None:
        """Publish a Slack event to the appropriate Kafka topic.

        Parameters
        ----------
        request_json
            The parsed JSON event published by Slack. Events and the Events API
            are described by Slack at https://api.slack.com/events.
        """
        # Different events have different schemas and are published to
        # different Kafka topics. Use the event.type field from the Slack
        # request to route the events's handling.
        if (
            "event" in request_json
            and request_json["event"]["type"] == SlackMessageType.message.value
        ):
            await self._publish_message_event(request_json)
        elif (
            "event" in request_json
            and request_json["event"]["type"]
            == SlackMessageType.app_mention.value
        ):
            await self._publish_app_mention_event(request_json)
        else:
            self._logger.debug("Did not parse Slack event")

    async def _publish_app_mention_event(
        self, request_json: dict[str, Any]
    ) -> None:
        """Publish a Slack ``app_mention`` event to Kafka."""
        try:
            event = SlackMessageEvent.model_validate(request_json)
        except Exception as e:
            self._logger.exception(
                "Could not parse Slack event", exc_info=e, raw=request_json
            )
            raise
        self._logger.debug(
            "Got a Slack app_mention event",
            event_type=event.event.type,
            slack_text=event.event.text,
            channel_id=event.event.channel,
            user_id=event.event.user,
        )

        # Create the Kafka key and value as Pydantic objects
        key = SquarebotSlackMessageKey.from_event(event)
        value = SquarebotSlackAppMentionValue.from_event(
            event=event, raw=request_json
        )

        # Produce message to Kafka
        await self._app_mentions_publisher.publish(
            message=value,
            key=key.to_key_bytes(),
            headers={"content-type": "application/json"},
        )

        self._logger.debug(
            "Published Slack app_mention event to Kafka",
            topic=self._config.app_mention_topic,
            value=value.model_dump(),
            key=key.model_dump(),
        )

    async def _publish_message_event(
        self, request_json: dict[str, Any]
    ) -> None:
        """Publish a Slack ``message`` event to Kafka."""
        try:
            event = SlackMessageEvent.model_validate(request_json)
        except Exception as e:
            self._logger.exception(
                "Could not parse Slack event", exc_info=e, raw=request_json
            )
            raise
        self._logger.debug(
            "Got a Slack message event",
            event_type=event.event.type,
            slack_text=event.event.text,
            channel_id=event.event.channel,
            channel_type=event.event.channel_type,
            user_id=event.event.user,
        )

        # Create the Kafka key and value as Pydantic objects
        key = SquarebotSlackMessageKey.from_event(event)
        value = SquarebotSlackMessageValue.from_event(
            event=event, raw=request_json
        )

        # Determine the Kafka topic based on the event type
        if event.event.channel_type is None:
            raise RuntimeError(
                "Null channel type should be handled by app_mention schema"
            )

        if event.event.channel_type == SlackChannelType.channel:
            topic = self._config.message_channels_topic
            publisher = self._channel_publisher
        elif event.event.channel_type == SlackChannelType.group:
            topic = self._config.message_groups_topic
            publisher = self._groups_publisher
        elif event.event.channel_type == SlackChannelType.im:
            topic = self._config.message_im_topic
            publisher = self._im_publisher
        elif event.event.channel_type == SlackChannelType.mpim:
            topic = self._config.message_mpim_topic
            publisher = self._mpim_publisher
        else:
            raise RuntimeError(
                f"Could not determine topic for Slack message event. "
                f"Channel type is {event.event.channel_type.value}"
            )

        # Produce message to Kafka
        await publisher.publish(
            message=value,
            key=key.to_key_bytes(),
            headers={"content-type": "application/json"},
        )

        self._logger.debug(
            "Published Slack message event to Kafka",
            topic=topic,
            value=value.model_dump(),
            key=key.model_dump(),
        )

    async def publish_interaction(
        self, interaction_payload: dict[str, Any]
    ) -> None:
        """Publish a Slack interaction payload to a Kafka topic.

        Parameters
        ----------
        interaction_payload
            The parsed JSON interaction payload published by Slack. Interaction
            payloads are described at
            https://api.slack.com/reference/interaction-payloads
        """
        if (
            "type" in interaction_payload
            and interaction_payload["type"] == "block_actions"
        ):
            action = SlackBlockActionsPayload.model_validate(
                interaction_payload
            )
            # Temporary placeholder; will serialize and publish to Kafka
            # in reality.
            self._logger.debug(
                "Got a Slack interaction",
                type=action.type,
                trigger_id=action.trigger_id,
                username=action.user.username,
                channel=action.channel.name if action.channel else None,
            )
        else:
            self._logger.debug("Did not parse Slack interaction")
            print(interaction_payload)  # noqa: T201
