"""Utilities for formatting Slack event messages as Avro-encoded messages.
"""

__all__ = ('SlackEventSerializer', 'load_event_schema', 'validate_avro_schema',
           'encode_slack_message')

from io import BytesIO
import json
from pathlib import Path

import fastavro
from kafkit.registry.serializer import PolySerializer


class SlackEventSerializer:
    """An Avro (Confluent Wire Format) serializer for Slack Events.

    Parameters
    ----------
    registry : `kafkit.registry.aiohttp.RegistryApi`
        Client for the Confluent Schema Registry.

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

    def __init__(self, *, registry):
        self._serializer = PolySerializer(registry=registry)

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
        schema = load_event_schema(event_type)
        return await self._serializer.serialize(message, schema=schema)


def load_event_schema(event_type):
    """Load an Avro schema for a Slack Events API event from the local app
    data.

    Parameters
    ----------
    event_type : `str`
        Name of an event type, such as ``"message"``. See
        https://api.slack.com/events for a listing. Not all events have
        Avro schemas in SQuaRE Bot.

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

    return schema


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
