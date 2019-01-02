__all__ = ('post_event',)

from aiohttp import web
from sqrbot.routes import routes


@routes.post('/event')
async def post_event(request):
    """Handle an event post by the Slack Events API.
    """
    logger = request['logger']
    slack_event = await request.json()
    logger.info('Got event', payload=slack_event)

    if slack_event['type'] == 'url_verification':
        return _handle_url_verification(request, slack_event)

    return web.json_response(status=200)


def _handle_url_verification(request, slack_event):
    """Handle an Events API ``url_verification`` request with a ``challenge``
    field to verify the app.
    """
    expected_token = request.config_dict['sqrbot-jr/slackVerificationToken']
    try:
        if slack_event['token'] != expected_token:
            return web.json_response(
                status=401,
                reason='Verification token does not match')
    except KeyError:
        return web.json_response(
            status=400,
            reason='"token" missing from request body')

    return web.json_response(
        {'challenge': slack_event['challenge']},
        status=200)
