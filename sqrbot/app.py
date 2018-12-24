"""Application factory for the aiohttp.web-based app.
"""

__all__ = ('create_app',)

from aiohttp import web

from .config import create_config

routes = web.RouteTableDef()


def create_app():
    """Create the aiohttp.web application.
    """
    print('called create_app')
    config = create_config()
    app = web.Application()
    app.update(config)
    app.add_routes(routes)
    print('created app')
    return app


@routes.get('/')
async def handler(request):
    name = request.config_dict['api.lsst.codes/name']
    return web.Response(text=name)
