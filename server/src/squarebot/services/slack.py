"""Slack service layer."""

from __future__ import annotations

import hashlib
import hmac
import math
import time
from typing import Any

from fastapi import HTTPException, Request, status
from structlog.stdlib import BoundLogger

from rubinobs.square.squarebot.models.kafka import (
    SquarebotSlackMessageKey,
    SquarebotSlackMessageValue,
)
from rubinobs.square.squarebot.models.slack import (
    SlackBlockAction,
    SlackChannelType,
    SlackMessageEvent,
    SlackMessageType,
)

from ..config import Configuration
from .kafkaproducer import PydanticKafkaProducer


class SlackService:
    """A service for processing with Slack messages and interactions."""

    def __init__(
        self,
        logger: BoundLogger,
        config: Configuration,
        kafka_producer: PydanticKafkaProducer,
    ) -> None:
        self._logger = logger
        self._config = config
        self._producer = kafka_producer

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
            )

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
        # Parse into the Slack message model
        if (
            "event" in request_json
            and request_json["event"]["type"] in SlackMessageType.__members__
        ):
            try:
                event = SlackMessageEvent.parse_obj(request_json)
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
            if event.event.type == SlackMessageType.app_mention:
                topic = self._config.app_mention_topic
            elif event.event.channel_type == SlackChannelType.channel:
                topic = self._config.message_channels_topic
            elif event.event.channel_type == SlackChannelType.group:
                topic = self._config.message_groups_topic
            elif event.event.channel_type == SlackChannelType.im:
                topic = self._config.message_im_topic
            elif event.event.channel_type == SlackChannelType.mpim:
                topic = self._config.message_mpim_topic
            else:
                raise RuntimeError(
                    f"Could not determine topic for Slack message event. "
                    f"Message type is {event.event.channel_type.value}"
                )

            await self._producer.send(
                topic=topic,
                value=value,
                key=key,
            )
            self._logger.debug(
                "Published Slack event to Kafka",
                topic=topic,
                value=value.dict(),
                key=key.dict(),
            )

        else:
            self._logger.debug("Did not parse Slack event")

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
            action = SlackBlockAction.parse_obj(interaction_payload)
            # Temporary placeholder; will serialize and publish to Kafka
            # in reality.
            self._logger.debug(
                "Got a Slack interaction",
                type=action.type,
                trigger_id=action.trigger_id,
                username=action.user.username,
                channel=action.channel.name,
            )
