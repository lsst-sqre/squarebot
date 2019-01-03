"""Utilities for formatting Slack event messages as Avro-encoded messages.
"""

__all__ = ('load_event_schema', 'validate_avro_schema')

import json
from pathlib import Path

import fastavro


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
