"""Application factory for the aiohttp.web-based app.
"""

__all__ = ('create_app',)

import asyncio
import logging
import os
from pathlib import Path
import ssl
import sys

from aiohttp import web, ClientSession
from aiokafka import AIOKafkaProducer
import structlog
from kafkit.registry.aiohttp import RegistryApi

from .config import create_config
from .routes import init_root_routes, init_routes
from .middleware import setup_middleware
from .avroformat import SlackEventSerializer, SlackInteractionSerializer
from .topics import configure_topics


def create_app():
    """Create the aiohttp.web application.
    """
    config = create_config()
    configure_logging(
        profile=config['api.lsst.codes/profile'],
        log_level=config['api.lsst.codes/logLevel'],
        logger_name=config['api.lsst.codes/loggerName'])

    root_app = web.Application()
    root_app.update(config)
    root_app.add_routes(init_root_routes())
    root_app.cleanup_ctx.append(init_http_session)
    root_app.cleanup_ctx.append(configure_kafka_ssl)
    if config['sqrbot-jr/enableSchemas']:
        root_app.cleanup_ctx.append(init_serializers)
    if config['sqrbot-jr/enableTopicConfig']:
        root_app.cleanup_ctx.append(init_topics)
    if config['sqrbot-jr/enableProducers']:
        root_app.cleanup_ctx.append(init_producer)

    # Create sub-app for the app's public APIs at the correct prefix
    prefix = '/' + root_app['api.lsst.codes/name']
    app = web.Application()
    setup_middleware(app)
    app.add_routes(init_routes())
    root_app.add_subapp(prefix, app)

    logger = structlog.get_logger(root_app['api.lsst.codes/loggerName'])
    logger.info('Started sqrbot')

    return root_app


def configure_logging(profile='development', log_level='info',
                      logger_name='sqrbot'):
    """Configure logging and structlog.
    """
    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setFormatter(logging.Formatter('%(message)s'))
    logger = logging.getLogger(logger_name)
    logger.addHandler(stream_handler)
    logger.setLevel(log_level.upper())

    if profile == 'production':
        # JSON-formatted logging
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Key-value formatted logging
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer()
        ]

    structlog.configure(
        processors=processors,
        # context_class=structlog.threadlocal.wrap_dict(dict),
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


async def configure_kafka_ssl(app):
    """Configure an SSL context for the Kafka client (if appropriate).

    Notes
    -----
    Use this function as a `cleanup context`_:

    .. code-block:: python

       app.cleanup_ctx.append(init_http_session)
    """
    logger = structlog.get_logger(app['api.lsst.codes/loggerName'])

    ssl_context_key = 'sqrbot-jr/kafkaSslContext'

    if app['sqrbot-jr/kafkaProtocol'] != 'SSL':
        app[ssl_context_key] = None
        return

    cluster_ca_cert_path = app['sqrbot-jr/clusterCaPath']
    client_ca_cert_path = app['sqrbot-jr/clientCaPath']
    client_cert_path = app['sqrbot-jr/clientCertPath']
    client_key_path = app['sqrbot-jr/clientKeyPath']

    if cluster_ca_cert_path is None:
        raise RuntimeError('Kafka protocol is SSL but cluster CA is not set')
    if client_cert_path is None:
        raise RuntimeError('Kafka protocol is SSL but client cert is not set')
    if client_key_path is None:
        raise RuntimeError('Kafka protocol is SSL but client key is not set')

    if client_ca_cert_path is not None:
        logger.info('Contatenating Kafka client CA and certificate files.')
        # Need to contatenate the client cert and CA certificates. This is
        # typical for Strimzi-based Kafka clusters.
        client_ca = Path(client_ca_cert_path).read_text()
        client_cert = Path(client_cert_path).read_text()
        new_client_cert = '\n'.join([client_cert, client_ca])
        new_client_cert_path = Path(os.getenv('APPDIR', '.')) / 'client.crt'
        new_client_cert_path.write_text(new_client_cert)
        client_cert_path = str(new_client_cert_path)

    # Create a SSL context on the basis that we're the client authenticating
    # the server (the Kafka broker).
    ssl_context = ssl.create_default_context(
        purpose=ssl.Purpose.SERVER_AUTH,
        cafile=cluster_ca_cert_path)
    # Add the certificates that the Kafka broker uses to authenticate us.
    ssl_context.load_cert_chain(
        certfile=client_cert_path,
        keyfile=client_key_path)
    app[ssl_context_key] = ssl_context

    logger.info('Created Kafka SSL context')

    yield


async def init_http_session(app):
    """Create an aiohttp.ClientSession and make it available as a
    ``'api.lsst.codes/httpSession'`` key on the application.

    Notes
    -----
    Use this function as a `cleanup context`_:

    .. code-block:: python

       python.cleanup_ctx.append(init_http_session)

    The session is automatically closed on shut down.

    Access the session:

    .. code-block:: python

        session = app['api.lsst.codes/httpSession']

    .. cleanup context:
       https://aiohttp.readthedocs.io/en/stable/web_reference.html#aiohttp.web.Application.cleanup_ctx
    """
    # Startup phase
    session = ClientSession()
    app['api.lsst.codes/httpSession'] = session
    yield

    # Cleanup phase
    await app['api.lsst.codes/httpSession'].close()


async def init_serializers(app):
    """Initialize the Avro serializers for Slack events and interactions.

    Notes
    -----
    Use this function as a `cleanup context
    <https://aiohttp.readthedocs.io/en/stable/web_reference.html#aiohttp.web.Application.cleanup_ctx>`_.

    To access the Events API serializer:

    .. code-block:: python

       app['sqrbot-jr/eventSerializer']

    To access the interaction callback serializer::

       app['sqrbot-jr/interactionSerializer']

    This function also pregisters schemas and subject compatibility
    configurations. See `sqrbot.avroformat.register`.
    """
    # Start up phase
    logger = structlog.get_logger(app['api.lsst.codes/loggerName'])
    logger.info('Setting up Avro serializers')

    registry = RegistryApi(
        session=app['api.lsst.codes/httpSession'],
        url=app['sqrbot-jr/registryUrl'])

    serializer = await SlackEventSerializer.setup(registry=registry, app=app)
    app['sqrbot-jr/eventSerializer'] = serializer
    logger.info('Finished setting up Avro serializer for Slack events')

    interactionSerializer = await SlackInteractionSerializer.setup(
        registry=registry, app=app)
    app['sqrbot-jr/interactionSerializer'] = interactionSerializer
    logger.info(
        'Finished setting up Avro serializer for Slack interaction payloads.')

    yield

    # Cleanup phase
    # (Nothing to do)


async def init_topics(app):
    """Initialize Kafka topics.

    See `sqrbot.topics.configure_topics`.
    """
    logger = structlog.get_logger(app['api.lsst.codes/loggerName'])
    logger.info('Configuring Kafka topics')

    configure_topics(app)

    logger.info('Finished configuring Kafka topics')
    yield

    # Cleanup phase (nothing to do)


async def init_producer(app):
    """Initialize and cleanup the aiokafka Producer instance

    Notes
    -----
    Use this function as a `cleanup context
    <https://aiohttp.readthedocs.io/en/stable/web_reference.html#aiohttp.web.Application.cleanup_ctx>`_.

    To access the producer:

    .. code-block:: python

       producer = app['sqrbot-jr/producer']
    """
    # Startup phase
    logger = structlog.get_logger(app['api.lsst.codes/loggerName'])
    logger.info('Starting Kafka producer')
    loop = asyncio.get_running_loop()
    producer = AIOKafkaProducer(
        loop=loop,
        bootstrap_servers=app['sqrbot-jr/brokerUrl'],
        ssl_context=app['sqrbot-jr/kafkaSslContext'],
        sasl_mechanism=app['sqrbot-jr/kafkaSasl'],
        security_protocol=app['sqrbot-jr/kafkaProtocol'])
    await producer.start()
    app['sqrbot-jr/producer'] = producer
    logger.info('Finished starting Kafka producer')

    yield

    # cleanup phase
    logger.info('Shutting down Kafka producer')
    await producer.stop()
