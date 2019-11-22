__all__ = ('post_event',)

from aiohttp import web

from sqrbot.routes import routes
from sqrbot.topics import map_event_to_topic
from sqrbot.verification import verify_request


@routes.post('/event')
async def post_event(request):
    """Handle an event post by the Slack Events API.
    """
    configs = request.config_dict

    logger = request['logger']
    # Verify the Slack signing secret on the request
    await verify_request(request)

    slack_event = await request.json()
    logger = logger.bind(payload=slack_event)
    logger.info('Got event')

    if slack_event['type'] == 'url_verification':
        return _handle_url_verification(request, slack_event)
    else:
        try:
            serializer = configs['sqrbot-jr/eventSerializer']
            producer = configs['sqrbot-jr/producer']
            data = await serializer.serialize(slack_event)
            topic_name = map_event_to_topic(slack_event, configs)
            await producer.send(topic_name, value=data)
            logger.debug('Sent Kafka message', topic=topic_name)
        except Exception:
            logger.exception("Failed to serialize and send event")
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
