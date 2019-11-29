"""Handle message interaction callbacks.
"""

__all__ = ('post_interaction',)

import json

from aiohttp import web

from sqrbot.routes import routes
from sqrbot.topics import get_interaction_topic_name
from sqrbot.verification import verify_request


@routes.post('/interaction')
async def post_interaction(request):
    """Handle an interaction post by the Slack API.
    """
    logger = request['logger']
    configs = request.config_dict

    # Verify the Slack signing secret on the request
    await verify_request(request)

    data = await request.post()
    payload = json.loads(data['payload'])
    logger.debug('Parsed interaction request', data=payload)

    try:
        serializer = configs['sqrbot-jr/interactionSerializer']
        producer = configs['sqrbot-jr/producer']
        data = await serializer.serialize(payload)
        topic_name = get_interaction_topic_name(configs)
        await producer.send(topic_name, value=data)
    except Exception:
        logger.exception("Failed to serialize and send Slack interaction")
    finally:
        # Always return a 200 so Slack knows we're still listening.
        return web.json_response(status=200)
