"""aiohttp.web middleware for sqrbot.
"""

__all__ = ("setup_middleware",)

from .logging import bind_logger


def setup_middleware(app):
    """Add sqrbot middleware to the application.

    Notes
    -----
    This function includes the following middleware, in order:

    1. `sqrbot.middleware.bind_logger`

    Examples
    --------
    Use it like this:

    .. code-block:: python

       app = web.Application()
       setup_middleware(app)
    """
    app.middlewares.append(bind_logger)
