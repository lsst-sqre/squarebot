__all__ = ('post_event',)

import hmac
import hashlib
import math
import time

from aiohttp import web
from sqrbot.routes import routes


@routes.post('/event')
async def post_event(request):
    """Handle an event post by the Slack Events API.
    """
    logger = request['logger']
    # Verify the Slack signing secret on the request
    await _verify_request(request)

    slack_event = await request.json()
    logger = logger.bind(payload=slack_event)
    logger.info('Got event')

    if slack_event['type'] == 'url_verification':
        return _handle_url_verification(request, slack_event)
    else:
        try:
            serializer = request.app['sqrbot-jr/serializer']
            data = await serializer.serialize(slack_event)
        except Exception as e:
            logger.error(
                "Failed to serialize event",
                error=str(e))
        finally:
            # Always return a 200 so Slack knows we're still listening.
            return web.json_response(status=200)


def _handle_url_verification(request, slack_event):
    """Handle an Events API ``url_verification`` request with a ``challenge``
    field to verify the app.

    Notes
    -----
    This assumes that the request's ``type`` is ``url_verification`` and that
    the request has already been verified.
    """
    return web.json_response(
        {'challenge': slack_event['challenge']},
        status=200)


async def _verify_request(request):
    """Verify the authenticity of a request from Slack using the signing
    secret method.

    See: https://api.slack.com/docs/verifying-requests-from-slack
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
