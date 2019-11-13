"""Configuration collection.
"""

__all__ = ('create_config',)

import os


def create_config():
    """Create a config mapping from defaults and environment variable
    overrides.

    Returns
    -------
    c : `dict`
        A configuration dictionary.

    Examples
    --------
    Apply the configuration to the aiohttp.web application::

        app = web.Application()
        app.update(create_config)
    """
    c = {}

    # Application run profile. 'development' or 'production'
    c['api.lsst.codes/profile'] = os.getenv(
        'API_LSST_CODES_PROFILE',
        'development').lower()

    # That name of the api.lsst.codes service, which is also the root path
    # that the app's API is served from.
    c['api.lsst.codes/name'] = os.getenv('API_LSST_CODES_NAME', 'sqrbot-jr')

    # The name of the logger, which should also be the name of the Python
    # package.
    c['api.lsst.codes/loggerName'] = os.getenv(
        'API_LSST_CODES_LOGGER_NAME', 'sqrbot')

    # Log level (INFO or DEBUG)
    c['api.lsst.codes/logLevel'] = os.getenv(
        'API_LSST_CODES_LOG_LEVEL',
        'info' if c['api.lsst.codes/profile'] == 'production' else 'debug'
    ).upper()

    # Enable schema management
    c['sqrbot-jr/enableSchemas'] \
        = bool(int(os.getenv('SQRBOTJR_ENABLE_SCHEMAS', "1")))

    # Enable producers
    c['sqrbot-jr/enableTopicConfig'] \
        = bool(int(os.getenv('SQRBOTJR_ENABLE_TOPIC_CONFIG', "1")))

    # Enable producers
    c['sqrbot-jr/enableProducers'] \
        = bool(int(os.getenv('SQRBOTJR_ENABLE_PRODUCERS', "1")))

    # Schema Registry hostname
    c['sqrbot-jr/registryUrl'] = os.getenv('SQRBOTJR_REGISTRY')

    # Kafka broker host
    c['sqrbot-jr/brokerUrl'] = os.getenv('SQRBOTJR_BROKER')

    # Kafka retention of Slack events in minutes
    c['sqrbot-jr/retentionMinutes'] = \
        os.getenv('SQRBOTJR_RETENTION_MINUTES', '30')

    # Kafka security protocol: PLAINTEXT or SSL
    c['sqrbot-jr/kafkaProtocol'] = os.getenv('SQRBOTJR_KAFKA_PROTOCOL')

    # TLS certificates for cluster + client for use with the SSL Kafka protocol
    c['sqrbot-jr/clusterCaPath'] = os.getenv('SQRBOTJR_KAFKA_CLUSTER_CA')
    c['sqrbot-jr/clientCaPath'] = os.getenv('SQRBOTJR_KAFKA_CLIENT_CA')
    c['sqrbot-jr/clientCertPath'] = os.getenv('SQRBOTJR_KAFKA_CLIENT_CERT')
    c['sqrbot-jr/clientKeyPath'] = os.getenv('SQRBOTJR_KAFKA_CLIENT_KEY')

    # Suffix to add to Schema Registry suffix names. This is useful when
    # deploying sqrbot-jr for testing/staging and you do not want to affect
    # the production subject and its compatibility lineage.
    c['sqrbot-jr/subjectSuffix'] = os.getenv('SQRBOTJR_SUBJECT_SUFFIX', '')

    # Compatibility level to apply to Schema Registry subjects. Use
    # NONE for testing and development, but prefer FORWARD_TRANSITIVE for
    # production.
    c['sqrbot-jr/subjectCompatibility'] \
        = os.getenv('SQRBOTJR_SUBJECT_COMPATIBILITY', 'FORWARD_TRANSITIVE')

    # Topic names
    c['sqrbot-jr/appMentionTopic'] = os.getenv(
        'SQRBOTJR_TOPIC_APP_MENTION', 'sqrbot.app_mention')
    c['sqrbot-jr/messageChannelsTopic'] = os.getenv(
        'SQRBOTJR_TOPIC_MESSAGE_CHANNELS', 'sqrbot.message.channels')
    c['sqrbot-jr/messageImTopic'] = os.getenv(
        'SQRBOTJR_TOPIC_MESSAGE_IM', 'sqrbot.message.im')
    c['sqrbot-jr/messageGroupsTopic'] = os.getenv(
        'SQRBOTJR_TOPIC_MESSAGE_GROUPS', 'sqrbot.message.groups')
    c['sqrbot-jr/messageMpimTopic'] = os.getenv(
        'SQRBOTJR_TOPIC_MESSAGE_MPIM', 'sqrbot.message.mpim')
    c['sqrbot-jr/interactionTopic'] = os.getenv(
        'SQRBOTJR_TOPIC_INTERACTION', 'sqrbot.interaction')

    # Slack signing secret
    c['sqrbot-jr/slackSigningSecret'] = os.getenv('SQRBOTJR_SLACK_SIGNING')

    # Slack bot token
    c['sqrbot-jr/slackToken'] = os.getenv('SQRBOTJR_SLACK_TOKEN')

    # Slack App ID
    c['sqrbot-jr/slackAppId'] = os.getenv('SQRBOTJR_SLACK_APP_ID')

    return c
