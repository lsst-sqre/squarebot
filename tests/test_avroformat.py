"""Tests for the sqrbot.avroformat module.
"""

from io import BytesIO
import json
from pathlib import Path

import pytest
import fastavro
import avro.schema  # official Avro library (for testing only)

from sqrbot.avroformat import (
    load_event_schema, get_desired_compatibility, list_event_schemas,
    list_interaction_types, load_interaction_schema, encode_slack_message,
    load_key_schema)


def validate_avro_schema(schema_object):
    """Validate an Avro schema using the avro package, which is stricter
    than fastavro.
    """
    avro.schema.Parse(json.dumps(schema_object))


@pytest.mark.parametrize(
    'event_type',
    [
        'message'
    ]
)
def test_load_event_schema(event_type):
    """Test the validity of event schemas loaded by
    sqrbot.avroformat.load_event_schema.
    """
    schema = load_event_schema(event_type)
    validate_avro_schema(schema)


@pytest.mark.parametrize(
    'name',
    [
        'event.message',
        'interaction',
    ]
)
def test_load_key_schema(name):
    """Test the validity of key schemas loaded by
    sqrbot.avroformat.load_key_schema.
    """
    schema = load_key_schema(name)
    validate_avro_schema(schema)


def test_load_event_schema_subject_suffix():
    """Test that a suffix gets added to the schema's name.
    """
    schema1 = load_event_schema('message')
    assert schema1['name'].endswith('_dev1') is False

    schema2 = load_event_schema('message', suffix='_dev1')
    assert schema2['name'].endswith('_dev1')


def test_get_desired_compatibility():
    """Test the get_desired_compatibility.
    """
    # Mock app (just a configuration)
    mockapp = {
        'sqrbot-jr/subjectSuffix': '',
        'sqrbot-jr/subjectCompatibility': 'FORWARD_TRANSITIVE'}
    assert get_desired_compatibility(mockapp) == 'FORWARD_TRANSITIVE'

    mockapp = {
        'sqrbot-jr/subjectSuffix': '',
        'sqrbot-jr/subjectCompatibility': 'NONE'}
    assert get_desired_compatibility(mockapp) == 'NONE'


def test_interaction_schemas():
    """Test schemas/interaction.json."""
    for interaction_type in list_interaction_types():
        print(f'interaction_type: {interaction_type}')
        schema = load_interaction_schema(interaction_type)
        validate_avro_schema(schema)


def test_list_event_schemas():
    event_names = list_event_schemas()
    assert 'message' in event_names


@pytest.mark.parametrize(
    'message_filename',
    [
        'message.im.json',
        'message.channels.json',
        'message.groups.json',
        'message.mpim.json',
        'app_mention.json',
    ]
)
def test_encode_message(message_filename):
    p = Path(__file__).parent / 'slack_messages' / 'message.im.json'
    message = json.loads(p.read_text())
    data = encode_slack_message(message)
    assert isinstance(data, bytes)

    # Try to read the message back
    event_type = message['event']['type']
    schema = load_event_schema(event_type)
    bytes_fh = BytesIO()
    bytes_fh.write(data)
    bytes_fh.seek(0)
    decoded_message = fastavro.schemaless_reader(bytes_fh, schema)
    # messages are not equal because the original data may have more fields
    # than the original message, or the avro-encoded message may have defaults
    # added to it.
    # assert decoded_message == message
    assert 'event' in decoded_message
