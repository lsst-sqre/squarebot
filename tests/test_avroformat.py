"""Tests for the sqrbot.avroformat module.
"""

import pytest

from sqrbot.avroformat import load_event_schema, validate_avro_schema


@pytest.mark.parametrize(
    'event_type',
    [
        'message.im'
    ]
)
def test_load_event_schema(event_type):
    """Test the validity of event schemas loaded by
    sqrbot.avroformat.load_event_schema.
    """
    schema = load_event_schema(event_type)
    validate_avro_schema(schema)

    assert schema['name'] == event_type
