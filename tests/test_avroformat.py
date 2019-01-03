"""Tests for the sqrbot.avroformat module.
"""

from io import BytesIO
import json
from pathlib import Path

import pytest
import fastavro

from sqrbot.avroformat import (load_event_schema, validate_avro_schema,
                               encode_slack_message)


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

    assert schema['name'] == event_type


@pytest.mark.parametrize(
    'message_filename',
    [
        'message.im.json',
        'message.channels.json',
        'message.groups.json',
        'message.mpim.json',
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
