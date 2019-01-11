"""Application factory for the aiohttp.web-based app.
"""

__all__ = ('create_app',)

import logging
import sys

from aiohttp import web, ClientSession
import structlog

from .config import create_config
from .routes import init_root_routes, init_routes
from .middleware import setup_middleware


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
