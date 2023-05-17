"""A FastAPI dependency that wraps multiple common dependencies."""

from dataclasses import dataclass
from typing import Optional

from aiokafka import AIOKafkaProducer
from fastapi import Depends, Request, Response
from httpx import AsyncClient
from kafkit.registry.manager import PydanticSchemaManager
from safir.dependencies.http_client import http_client_dependency
from safir.dependencies.logger import logger_dependency
from structlog.stdlib import BoundLogger

from squarebot.dependencies.schemamanager import (
    pydantic_schema_manager_dependency,
)

from ..config import Configuration, config
from ..services.kafkaproducer import PydanticKafkaProducer
from ..services.slack import SlackService
from .aiokafkaproducer import kafka_producer_dependency

__all__ = ["RequestContext", "context_dependency"]


@dataclass
class RequestContext:
    """Holds the incoming request and its surrounding context.
    The primary reason for the existence of this class is to allow the
    functions involved in request processing to repeatedly rebind the request
    logger to include more information, without having to pass both the
    request and the logger separately to every function.
    """

    request: Request
    """The incoming request."""

    response: Response
    """The response (useful for setting response headers)."""

    config: Configuration
    """SQuaRE Bot's configuration."""

    slack: SlackService
    """The Slack service layer."""

    logger: BoundLogger
    """The request logger, rebound with discovered context."""

    http_client: AsyncClient
    """An HTTPX client."""

    kafka_producer: PydanticKafkaProducer
    """A Kafka producer that sends managed Pydantic models."""

    schema_manager: PydanticSchemaManager
    """A Kafkit Pydantic Schema Manager."""

    def rebind_logger(self, **values: Optional[str]) -> None:
        """Add the given values to the logging context.
        Also updates the logging context stored in the request object in case
        the request context later needs to be recreated from the request.
        Parameters
        ----------
        **values : `str` or `None`
            Additional values that should be added to the logging context.
        """
        self.logger = self.logger.bind(**values)


async def context_dependency(
    request: Request,
    response: Response,
    logger: BoundLogger = Depends(logger_dependency),
    http_client: AsyncClient = Depends(http_client_dependency),
    kafka_producer: AIOKafkaProducer = Depends(kafka_producer_dependency),
    schema_manager: PydanticSchemaManager = Depends(
        pydantic_schema_manager_dependency
    ),
) -> RequestContext:
    """Provides a RequestContext as a dependency."""
    pydantic_kafka_producer = PydanticKafkaProducer(
        producer=kafka_producer, schema_manager=schema_manager
    )
    slack_service = SlackService(
        logger=logger, config=config, kafka_producer=pydantic_kafka_producer
    )
    return RequestContext(
        request=request,
        response=response,
        config=config,
        slack=slack_service,
        logger=logger,
        http_client=http_client,
        kafka_producer=pydantic_kafka_producer,
        schema_manager=schema_manager,
    )
