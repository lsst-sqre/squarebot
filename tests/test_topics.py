"""Tests for the sqrbot.topics module.
"""

from sqrbot.topics import name_topic


def test_name_topic():
    """Test the sqrbot.topics.name_topic function.
    """
    app = {'sqrbot-jr/stagingVersion': ''}
    assert name_topic('app_mention', app) == 'sqrbot-app_mention'

    app = {'sqrbot-jr/stagingVersion': 'dev'}
    assert name_topic('app_mention', app) == 'sqrbot-app_mention-dev'
