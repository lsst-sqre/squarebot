"""Tests for the sqrbot.topics module.
"""

from sqrbot.topics import event_to_topic_name, identify_slack_event


def test_event_to_topic_name():
    """Test the sqrbot.topics.event_to_topic_name function.
    """
    app = {'sqrbot-jr/stagingVersion': '',
           'sqrbot-jr/appMentionTopic': 'sqrbot.app_mention'}
    assert event_to_topic_name('app_mention', app) == 'sqrbot.app_mention'

    app = {'sqrbot-jr/stagingVersion': 'dev',
           'sqrbot-jr/appMentionTopic': 'sqrbot.app_mention'}
    assert event_to_topic_name('app_mention', app) == 'sqrbot.app_mention'


def test_identify_app_mention():
    event = {
        'event': {
            'type': 'app_mention'
        }
    }
    assert identify_slack_event(event) == 'app_mention'


def test_identify_message_channels():
    event = {
        'event': {
            'type': 'message',
            'channel_type': 'channel'
        }
    }
    assert identify_slack_event(event) == 'message.channels'


def test_identify_message_im():
    event = {
        'event': {
            'type': 'message',
            'channel_type': 'im'
        }
    }
    assert identify_slack_event(event) == 'message.im'


def test_identify_message_mpim():
    event = {
        'event': {
            'type': 'message',
            'channel_type': 'mpim'
        }
    }
    assert identify_slack_event(event) == 'message.mpim'


def test_identify_message_groups():
    event = {
        'event': {
            'type': 'message',
            'channel_type': 'group'
        }
    }
    assert identify_slack_event(event) == 'message.groups'
