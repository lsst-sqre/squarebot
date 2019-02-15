"""Handle message interaction callbacks.
"""

__all__ = ('post_interaction',)

import json

from aiohttp import web

from sqrbot.routes import routes
from sqrbot.verification import verify_request


@routes.post('/interaction')
async def post_interaction(request):
    """Handle an interaction post by the Slack API.
    """
    logger = request['logger']

    # Verify the Slack signing secret on the request
    await verify_request(request)

    data = await request.post()
    payload = json.loads(data['payload'])
    logger.info('Parsed interaction request', data=payload)

    # Always return a 200 so Slack knows we're still listening.
    return web.json_response(status=200)
