"""Application factory for the aiohttp.web-based app.
"""

__all__ = ('create_app',)

from aiohttp import web

from .config import create_config
from .routes import init_root_routes, init_routes


def create_app():
    """Create the aiohttp.web application.
    """
    print('called create_app')
    config = create_config()
    root_app = web.Application()
    root_app.update(config)
    root_app.add_routes(init_root_routes())

    # Create sub-app for the app's public APIs at the correct prefix
    prefix = '/' + root_app['api.lsst.codes/name']
    app = web.Application()
    app.add_routes(init_routes())
    root_app.add_subapp(prefix, app)

    print('created app')
    return root_app
