"""A FastAPI dependency that wraps multiple common dependencies."""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request
from safir.dependencies.logger import logger_dependency
from structlog.stdlib import BoundLogger

from ..factory import Factory, ProcessContext

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

    logger: BoundLogger
    """The request logger, rebound with discovered context."""

    factory: Factory
    """A factory for creating services and other components."""

    def rebind_logger(self, **values: str | None) -> None:
        """Add the given values to the logging context.
        Also updates the logging context stored in the request object in case
        the request context later needs to be recreated from the request.

        Parameters
        ----------
        **values : `str` or `None`
            Additional values that should be added to the logging context.
        """
        self.logger = self.logger.bind(**values)


class ContextDependency:
    """Provide a per-request context as a FastAPI dependency.

    Each request gets a `RequestContext`.  To save overhead, the portions of
    the context that are shared by all requests are collected into the single
    process-global `~gafaelfawr.factory.ProcessContext` and reused with each
    request.
    """

    def __init__(self) -> None:
        self._process_context: ProcessContext | None = None

    async def __call__(
        self,
        request: Request,
        logger: Annotated[BoundLogger, Depends(logger_dependency)],
    ) -> RequestContext:
        """Create a per-request context and return it."""
        factory = self.create_factory(logger)
        return RequestContext(
            request=request,
            logger=logger,
            factory=factory,
        )

    @property
    def process_context(self) -> ProcessContext:
        """Context that is shared by all requests for the life of the app."""
        if not self._process_context:
            raise RuntimeError("ContextDependency not initialized")
        return self._process_context

    async def initialize(self) -> None:
        """Initialize the process-wide shared context.

        Parameters
        ----------
        config
            Application configuration.
        """
        if self._process_context:
            await self._process_context.aclose()
        self._process_context = await ProcessContext.create()

    def create_factory(self, logger: BoundLogger) -> Factory:
        """Create a factory for use outside a request context."""
        return Factory(
            logger=logger,
            process_context=self.process_context,
        )

    async def aclose(self) -> None:
        """Clean up the per-process configuration."""
        if self._process_context:
            await self._process_context.aclose()
        self._process_context = None


context_dependency = ContextDependency()
"""The dependency that will return the per-request context."""
