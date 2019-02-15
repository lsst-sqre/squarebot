"""Common code for verifying requests from Slack.
"""

__all__ = ('verify_request',)

import hmac
import hashlib
import math
import time

from aiohttp import web


async def verify_request(request):
    """Verify the authenticity of a request from Slack using the signing
    secret method.

    See: https://api.slack.com/docs/verifying-requests-from-slack

    Parameters
    ----------
    request
        The request object. This function must be run inside a request handler.

    Raises
    ------
    aiohttp.web.HTTPException
        Raised if the ``X-Slack-Signature`` header could not be verified.
    """
    timestamp = request.headers['X-Slack-Request-Timestamp']

    if math.fabs(time.time() - float(timestamp)) > 300.:
        # The request timestamp is more than five minutes from local time.
        # It could be a replay attack, so let's ignore it.
        raise web.HTTPException(
            status=400,
            reason='X-Slack-Request-Timestamp is older than 5 minutes.'
        )

    # Ensure that no special decoding is done on the body
    body_bytes = await request.read()
    body = body_bytes.decode(encoding='utf-8')

    signing_secret = request.config_dict['sqrbot-jr/slackSigningSecret']

    base_signature = f'v0:{timestamp}:{body}'
    signature_hash = 'v0=' + hmac.new(
        signing_secret.encode(),
        msg=base_signature.encode(),
        digestmod=hashlib.sha256).hexdigest()

    if hmac.compare_digest(
            signature_hash, request.headers['X-Slack-Signature']):
        return True
    else:
        raise web.HTTPException(
            status=400,
            reason='Could not successfully verify X-Slack-Signature'
        )
