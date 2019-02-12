"""Utilities for formatting Slack event messages as Avro-encoded messages.
"""

__all__ = ('SlackEventSerializer', 'load_event_schema', 'validate_avro_schema',
           'list_event_schemas', 'preregister_schemas',
           'encode_slack_message')

import functools
from io import BytesIO
import json
from pathlib import Path

import structlog
import fastavro
from kafkit.registry.serializer import PolySerializer


class SlackEventSerializer:
    """An Avro (Confluent Wire Format) serializer for Slack Events.

    Parameters
    ----------
    registry : `kafkit.registry.aiohttp.RegistryApi`
        Client for the Confluent Schema Registry.
    staging_version `str`, optional
        If the application is running in a staging environment, this is the
        name of the staging version. This should be set through the
        ``sqrbot-jr/stagingVersion`` configuration key on the app. Leave as
        `None` if the application is not in staging.

    Notes
    -----
    This serializer takes the JSON body of an Event payload from the Slack API
    and emits an Avro-encoded message in the Confluent Wire Format (which
    includes a prefix that identifies the schema used to encode the message).

    It follows this algorithm:

    1. Identifies the type of the event based on the `event.type` fields of the
       event payload.
    2. Gets the Avro schema for that event type from the app's data. This way
       the app always serializes data in a format it is tested with.
    3. Through the `kafkit.registry.serializer.PolySerializer`, the schema is
       registered with the broker so a unique ID is known.
    4. The serializer encodes the message.
    """

    def __init__(self, *, registry, staging_version=None):
        self._serializer = PolySerializer(registry=registry)
        self._staging_version = staging_version

    async def serialize(self, message):
        """Serialize a Slack event.

        Parameters
        ----------
        message : `dict`
            The original JSON payload of a Slack Event, including the wrapper.
            See https://api.slack.com/types/event.

        Returns
        -------
        data : `bytes
            Data encoded in the `Confluent Wire Format
            <https://docs.confluent.io/current/schema-registry/docs/serializer-formatter.html#wire-format>`_,
            ready to be sent to a Kafka broker.
        """
        event_type = message['event']['type']
        schema = load_event_schema(event_type,
                                   suffix=self._staging_version)
        return await self._serializer.serialize(message, schema=schema)


@functools.lru_cache()
def load_event_schema(event_type, suffix=None):
    """Load an Avro schema for a Slack Events API event from the local app
    data.

    This function is memoized so that repeated calls are fast.

    Parameters
    ----------
    event_type : `str`
        Name of an event type, such as ``"message"``. See
        https://api.slack.com/events for a listing. Not all events have
        Avro schemas in SQuaRE Bot.
    suffix : `str`, optional
        A suffix to add to the schema's name. This is typically used to create
        "staging" schemas, therefore "staging subjects" in the Schema Registry.

    Returns
    -------
    schema : `dict`
        A schema object.

    Notes
    -----
    This function loads schemas from the app's package data, rather from a
    schema registry service. The wrapper schema is the
    ``sqrbot/schemas/event.json`` file, while schemas for each type of event
    are in the ``sqrbot/schemas/events`` directory. This function inserts
    the event-specific schema into the ``events`` field of the wrapper and
    also sets the wrapper schemas name to the name of the event, such as
    ``message``.
    """
    # Normalize similar event types that share a common schema
    if event_type in ('app_mention', 'message', 'message.channels',
                      'message.im', 'message.groups', 'message.mpim'):
        event_type = 'message'

    schemas_dir = Path(__file__).parent / 'schemas'
    wrapper_path = schemas_dir / 'event.json'
    event_path = schemas_dir / 'events' / f'{event_type}.json'

    schema = json.loads(wrapper_path.read_text())
    event_schema = json.loads(event_path.read_text())

    # Insert the event schema into the wrapper schema
    inserted = False
    for field in schema['fields']:
        if field['name'] == 'event':
            field['type'] = event_schema
            inserted = True
            break
    if not inserted:
        raise RuntimeError('Wrapper schema does not have an `event` field.')

    # Make the overall schema take on the name of the event record.
    schema['name'] = event_schema['name']

    if suffix:
        schema['name'] = '-'.join((schema['name'], suffix))

    return fastavro.parse_schema(schema)


@functools.lru_cache()
def list_event_schemas():
    """List the events with schemas in the local package.

    Returns
    -------
    events : `list` [`str`]
        List of Slack event names with available schemas.

    Notes
    -----
    This function looks for schema json files in the
    ``sqrbot/schemas/events`` directory of the package. Each schema is named
    after a Slack event type.

    This function is cached, so repeated calls consume no additional IO.
    """
    event_schemas_dir = Path(__file__).parent / 'schemas' / 'events'
    schema_paths = event_schemas_dir.glob('*.json')
    return [p.stem for p in schema_paths]


async def preregister_schemas(registry, app):
    """Register schemas and ensure compatibility requirements.

    Parameters
    ----------
    registry : `kafkit.registry.aiohttp.RegistryApi`
        A Schema Registry client.
    app : `aiohttp.web.Application`
        The application instance.

    Notes
    -----
    This function iterates through all available schemas (`list_event_schemas`)
    and ensures that those schemas are registered under subjects in the schema
    registry. Subject names are determined from the fully-qualified ``name``
    field of the schema. Finally this function also ensures that the
    compatibility requirement on the subject is at the desired level
    (see `get_desired_compatibility`).

    This function responds to the ``sqrbot-jr/stagingVersion`` configuration
    variable. If that configuration is set (not `None`):

    - Schemas names have the value of ``sqrbot-jr/stagingVersion`` as suffix
      on the name.
    - Subjects names likewise have the suffix.
    - The compatibility requirements are ``"NONE"``. See
      `get_desired_compatibility`.
    """
    logger = structlog.get_logger(app['api.lsst.codes/loggerName'])

    desired_compat = get_desired_compatibility(app)

    logger.info(
        'Internally supported event schemas',
        names=list_event_schemas())
    for name in list_event_schemas():
        schema = load_event_schema(
            name,
            suffix=app['sqrbot-jr/stagingVersion'])

        schema_id = await registry.register_schema(schema)
        logger.info('Registered schema', subject=schema['name'], id=schema_id)

        subject_name = schema['name']
        subject_config = await registry.get('/config{/subject}')

        if subject_config['compatibility'] != desired_compat:
            await registry.put(
                '/config{/subject}',
                url_vars={'subject': subject_name},
                data={'compatibility': desired_compat})
            logger.info(
                'Reset subject compatibility level',
                subject=schema['name'],
                level=desired_compat)
        else:
            logger.info(
                'Existing subject compatibility level is good',
                subject=schema['name'],
                level=subject_config['compatibility'])


def get_desired_compatibility(app):
    """Get the desired compatibility configuration for subjects given the
    application configuration.

    Parameters
    ----------
    app : `aiohttp.web.Application`
        The application instance.

    Returns
    -------
    compatibility : `str`
        The Schema Registry compatibility level. The value is one of:

        ``"NONE"``
            If the ``sqrbot-jr/stagingVersion`` app config is set, then no
            compatiblility is required on the subject since it's a
            "staging" subject used for testing.
        ``"FORWARD_TRANSITIVE"``
            If ``sqrbot-jr/stagingVersion`` app config **is not** set, then
            the subjects must have ``"FORWARD_TRANSITIVE"`` compatibility,
            following the SQuaRE Events best practices.
    """
    if app['sqrbot-jr/stagingVersion'] == '':
        return 'FORWARD_TRANSITIVE'
    else:
        return 'NONE'


def validate_avro_schema(schema):
    """Validate that a schema object is an Avro schema.

    Parameters
    ----------
    schema : `dict`
        A schema object.

    Raises
    ------
    fastavro.SchemaParseException
        Raised if the schema is not valid.
    """
    fastavro.parse_schema(schema)


def encode_slack_message(message):
    """Encode a Slack message in Avro, using a schema that is automatically
    picked for the message's type.

    Parameters
    ----------
    message : `dict`
        A Slack message (parsed from JSON into a dictionary).

    Returns
    -------
    encoded : `bytes`
        The Avro-encoded message.
    """
    if message['type'] != 'event_callback':
        raise RuntimeError(f"message type is {message['type']}")

    event_type = message['event']['type']
    schema = fastavro.parse_schema(load_event_schema(event_type))

    binary_fh = BytesIO()
    fastavro.schemaless_writer(
        binary_fh,
        schema,
        message
    )
    binary_fh.seek(0)
    return binary_fh.read()
