"""Kafka topic management.
"""

__all__ = ('name_topic', 'KNOWN_SLACK_EVENTS')


KNOWN_SLACK_EVENTS = set([
    'app_mention', 'message.im', 'message.mpim', 'message.groups',
    'message.channels'])
"""The Slack events that SQuaRE Bot, Jr works with.

See the `Slack Event Types documentation <https://api.slack.com/events>`_ for
more information about specific events.
"""


def name_topic(slack_event_type, app):
    """Name the SQuaRE Events Kafka topic for a given Slack event type.

    Parameters
    ----------
    slack_event_type : `str`
        The name of the Slack event. This should be an item from
        `KNOWN_SLACK_EVENTS`.
    app : `aiohttp.web.Application`
        The application instance.

    Returns
    -------
    topic_name : `str`
        The name of the topic. The format is generally::

            sqrbot-{{slack_event_type}}

        If the ``sqrbot-jr/stagingVersion`` application configuration is
        set, then the name is also added as a suffix::

            sqrbot-{{slack_event_type}}-{{stagingVersion}}
    """
    if app['sqrbot-jr/stagingVersion'] is not None:
        topic_name = (
            f'sqrbot-{slack_event_type}'
            f'-{app["sqrbot-jr/stagingVersion"]}'
        )
    else:
        topic_name = f'sqrbot-{slack_event_type}'

    return topic_name
