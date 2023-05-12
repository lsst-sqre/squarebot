"""Application factory for SQuaRE Bot.

Notes
-----
Be aware that, following the normal pattern for FastAPI services, the app is
constructed when this module is loaded and is not deferred until a function is
called.
"""

from __future__ import annotations

from importlib.metadata import metadata, version

from fastapi import FastAPI
from safir.dependencies.http_client import http_client_dependency
from safir.logging import configure_logging, configure_uvicorn_logging
from safir.middleware.x_forwarded import XForwardedMiddleware
from structlog import get_logger

from .config import config
from .dependencies.aiokafkaproducer import kafka_producer_dependency
from .dependencies.registryapi import registry_api_dependency
from .dependencies.schemamanager import pydantic_schema_manager_dependency
from .handlers.external.handlers import external_router
from .handlers.internal.handlers import internal_router

__all__ = ["app"]


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
)
"""The main FastAPI application for squarebot."""

# Attach the routers.
app.include_router(internal_router)
app.include_router(external_router, prefix=config.path_prefix)

# Set up middleware
app.add_middleware(XForwardedMiddleware)


@app.on_event("startup")
async def startup_event() -> None:
    """Application start-up hook."""
    logger = get_logger()
    logger.info("Square Bot is starting up.")

    http_client = await http_client_dependency()

    # Initialize the Confluent Schema Registry client
    await registry_api_dependency.initialize(
        http_client=http_client, registry_url=config.registry_url
    )
    registry_api = await registry_api_dependency()

    # Initialize the Pydantic Schema Manager and register models
    await pydantic_schema_manager_dependency.initialize(
        registry_api=registry_api,
        models=[],
        suffix=config.subject_suffix,
        compatibility=config.subject_compatibility,
    )

    # Initialize the Kafka producer
    await kafka_producer_dependency.initialize(config.kafka)

    logger.info("Square Bot start up complete.")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Application shut-down hook."""
    logger = get_logger()
    await kafka_producer_dependency.stop()
    await http_client_dependency.aclose()
    logger.info("Square Bot shut down up complete.")
