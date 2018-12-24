"""Application factory for the aiohttp.web-based app.
"""

from aiohttp import web

routes = web.RouteTableDef()


def create_app():
    print('called create_app')
    app = web.Application()
    app.add_routes(routes)
    print('created app')
    return app


@routes.get('/')
async def handler(request):
    return web.Response(text="Hello world")
