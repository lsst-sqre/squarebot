"""Application factory for SQuaRE Bot.

Notes
-----
Be aware that, following the normal pattern for FastAPI services, the app is
constructed when this module is loaded and is not deferred until a function is
called.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from importlib.metadata import metadata, version

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from safir.dependencies.http_client import http_client_dependency
from safir.logging import configure_logging, configure_uvicorn_logging
from safir.middleware.x_forwarded import XForwardedMiddleware
from structlog import get_logger

from .config import config
from .dependencies.requestcontext import context_dependency
from .handlers.external.handlers import external_router
from .handlers.internal.handlers import internal_router
from .kafkarouter import kafka_router

__all__ = ["app", "create_openapi"]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Set up and tear down the application."""
    # Any code here will be run when the application starts up.
    logger = get_logger()
    logger.info("Square Bot is starting up.")

    logger.info(
        "Kafka topic configuration",
        slack={
            "app_mention": config.app_mention_topic,
            "message_channels": config.message_channels_topic,
            "message_im": config.message_im_topic,
            "message_groups": config.message_groups_topic,
            "message_mpim": config.message_mpim_topic,
            "interaction": config.interaction_topic,
        },
    )

    await context_dependency.initialize()

    async with kafka_router.lifespan_context(app):
        logger.info("Square Bot start up complete.")
        yield

    # Any code here will be run when the application shuts down.
    await http_client_dependency.aclose()
    await context_dependency.aclose()
    logger.info("Square Bot shut down up complete.")


configure_logging(
    profile=config.profile,
    log_level=config.log_level,
    name="squarebot",
)
configure_uvicorn_logging(config.log_level)

app = FastAPI(
    title="SQuaRE Bot",
    description=metadata("squarebot")["Summary"],
    version=version("squarebot"),
    openapi_url=f"{config.path_prefix}/openapi.json",
    docs_url=f"{config.path_prefix}/docs",
    redoc_url=f"{config.path_prefix}/redoc",
    lifespan=lifespan,
)
"""The main FastAPI application for squarebot."""

# Attach the routers.
app.include_router(internal_router)
app.include_router(external_router, prefix=config.path_prefix)
app.include_router(kafka_router)

# Set up middleware
app.add_middleware(XForwardedMiddleware)


def create_openapi() -> str:
    """Create the OpenAPI spec for static documentation."""
    spec = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    return json.dumps(spec)
