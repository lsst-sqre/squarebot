"""Handlers for the index view, `/sqrbot/`.
"""

__all__ = ('get_index',)

from aiohttp import web
from sqrbot.routes import routes


@routes.get('/')
async def get_index(request):
    logger = request['logger']
    logger.info('Logged message', somekey='somevalue')
    name = request.config_dict['api.lsst.codes/name']
    return web.Response(text=name)
