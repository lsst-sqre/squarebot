"""An HTTP client that acts like a Slack API server sending signed events and
interactions.
"""

from __future__ import annotations

import json
from time import time
from typing import Any

from httpx import AsyncClient, Response

from squarebot.config import config
from squarebot.services.slack import SlackService


class SlackServer:
    """A mock Slack API server that can send signed events, like the
    real Slack API.

    Parameters
    ----------
    client
        The HTTP client for the test session.
    """

    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    async def post(
        self,
        path: str,
        *,
        json_data: Any,
        signed: bool = True,
        timestamped: bool = True,
        bad_timestamp: bool = False,
        bad_signature: bool = False,
    ) -> Response:
        """Send a POST request events to the app like the Slack API server with
        control over the success of the message signing.

        Parameters
        ----------
        path
            The URL path to the Squarebot API.
        json_data
            The JSON message body send as the Slack API; typically a `dict`.
        signed
            When true, enable the Slack message signing process (setting
            the `X-Slack-Signature`). See
            https://api.slack.com/authentication/verifying-requests-from-slack
        timestamped
            When True, the ``X-Slack-Request-Timestamp`` is set.
        bad_timestamp
            When True, the ``X-Slack-Request-Timestamp`` is incorrectly set.
        bad_signature
            When True, the ``X-Slack-Signature`` is incorrectly set.

        Returns
        -------
        Response
            The response to the client request.
        """
        body = json.dumps(json_data)
        headers: dict[str, str] = {}
        timestamp = str(int(time()))
        if bad_timestamp:
            # throw off the timestamp to force an error
            timestamp = str(int(time()) + 1000)

        if timestamped:
            headers["X-Slack-Request-Timestamp"] = timestamp
        if signed:
            signing_secret = config.slack_signing_secret.get_secret_value()
            if bad_signature:
                # throw off the signature to force an error
                signing_secret = "wrong"
            slack_signature = SlackService.compute_slack_signature(
                signing_secret, body, timestamp
            )
            headers["X-Slack-Signature"] = slack_signature
        return await self._client.post(path, content=body, headers=headers)
