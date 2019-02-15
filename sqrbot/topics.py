"""Kafka topic management.
"""

__all__ = ('map_event_to_topic', 'identify_slack_event', 'event_to_topic_name',
           'KNOWN_SLACK_EVENTS')

from confluent_kafka.admin import AdminClient, NewTopic
import structlog


KNOWN_SLACK_EVENTS = set([
    'app_mention', 'message.im', 'message.mpim', 'message.groups',
    'message.channels'])
"""The Slack events that SQuaRE Bot, Jr works with.

See the `Slack Event Types documentation <https://api.slack.com/events>`_ for
more information about specific events.
"""


def map_event_to_topic(event, app):
    """Map a Slack event object to a Kafka topic name.

    Parameters
    ----------
    event : `dict`
        The Slack event object.
    app : `aiohttp.web.Application` or `dict`
        The application instance or just the configuration from it.

    Returns
    -------
    topic_name : `str`
        The name of the topic. The format is generally::

            sqrbot-{{slack_event_type}}

        If the ``sqrbot-jr/stagingVersion`` application configuration is
        set, then the name is also added as a suffix::

            sqrbot-{{slack_event_type}}-{{stagingVersion}}
    """
    event_type = identify_slack_event(event)
    return event_to_topic_name(event_type, app)


def identify_slack_event(event):
    """Identify the Slack event type given an event object.

    Parameters
    ----------
    event : `dict`
        The Slack event object.

    Returns
    -------
    slack_event_type : `str`
        The name of the slack event, one of https://api.slack.com/events.
    """
    primary_type = event['event']['type']
    if primary_type == 'message':
        channel_type = event['event']['channel_type']
        if channel_type == 'channel':
            return 'message.channels'
        if channel_type == 'im':
            return 'message.im'
        elif channel_type == 'group':
            return 'message.groups'
        elif channel_type == 'mpim':
            return 'message.mpim'
        else:
            raise RuntimeError(f'Unknown channel type {channel_type!r}')
    else:
        return primary_type


def event_to_topic_name(slack_event_type, app):
    """Name the SQuaRE Events Kafka topic for a given Slack event type.

    Parameters
    ----------
    slack_event_type : `str`
        The name of the Slack event. This should be an item from
        `KNOWN_SLACK_EVENTS`.
    app : `aiohttp.web.Application` or `dict`
        The application instance or just the configuration from it.

    Returns
    -------
    topic_name : `str`
        The name of the topic. The format is generally::

            sqrbot-{{slack_event_type}}

        If the ``sqrbot-jr/stagingVersion`` application configuration is
        set, then the name is also added as a suffix::

            sqrbot-{{slack_event_type}}-{{stagingVersion}}
    """
    if app['sqrbot-jr/stagingVersion']:
        topic_name = (
            f'sqrbot-{slack_event_type}'
            f'-{app["sqrbot-jr/stagingVersion"]}'
        )
    else:
        topic_name = f'sqrbot-{slack_event_type}'

    return topic_name


def configure_topics(app):
    """Create Kafka topics.

    This function is generally called at app startup.

    Parameters
    ----------
    app : `aiohttp.web.Application`
        The application instance.

    Notes
    -----
    This function registers any topics that SQuaRE Bot Jr produces that don't
    already exist. The topics correspond one-to-one with Slack events that
    SQuaRE Bot Jr listens to. These topics are hard-coded at
    `KNOWN_SLACK_EVENTS`

    If the ``sqrbot-jr/stagingVersion`` is set, any topics created will have
    that staging version as a name suffix.
    """
    logger = structlog.get_logger(app['api.lsst.codes/loggerName'])

    default_num_partitions = 1
    default_replication_factor = 3

    client = AdminClient({'bootstrap.servers': app['sqrbot-jr/brokerUrl']})

    # First list existing topics
    metadata = client.list_topics(timeout=10)
    existing_topic_names = [t for t in metadata.topics.keys()]

    # Create any topics that don't already exist
    new_topics = []
    for slack_event in KNOWN_SLACK_EVENTS:
        topic_name = event_to_topic_name(slack_event, app)
        if topic_name in existing_topic_names:
            topic = metadata.topics[topic_name]
            partitions = [p for p in iter(topic.partitions.values())]
            logger.info(
                'Topic exists',
                topic=topic_name,
                partitions=len(topic.partitions),
                replication_factor=len(partitions[0].replicas))
            continue
        new_topics.append(NewTopic(
            topic_name,
            num_partitions=default_num_partitions,
            replication_factor=default_replication_factor))

    if len(new_topics) > 0:
        fs = client.create_topics(new_topics)
        for topic_name, f in fs.items():
            try:
                f.result()  # The result itself is None
                logger.info(
                    'Created topic',
                    topic=topic_name,
                    partitions=default_num_partitions)
            except Exception as e:
                logger.error(
                    'Failed to create topic',
                    topic=topic_name, error=str(e))
                raise
