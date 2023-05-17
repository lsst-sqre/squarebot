"""A FastAPI dependency that provides an aiokafka Producer."""

import aiokafka  # patched for testing

from squarebot.config import KafkaConnectionSettings

__all__ = ["kafka_producer_dependency", "AioKafkaProducerDependency"]


class AioKafkaProducerDependency:
    """A FastAPI dependency that provides an aiokafka Producer."""

    def __init__(self) -> None:
        self._producer: aiokafka.AIOKafkaProducer | None = None

    async def initialize(self, settings: KafkaConnectionSettings) -> None:
        """Initialize the dependency (call during FastAPI startup)."""
        self._producer = aiokafka.AIOKafkaProducer(
            bootstrap_servers=settings.bootstrap_servers,
            # client_id=TODO,
            security_protocol=str(settings.security_protocol),
            ssl_context=settings.ssl_context,
            sasl_mechanism=str(settings.sasl_mechanism),
            sasl_plain_password=(
                settings.sasl_password.get_secret_value()
                if settings.sasl_password
                else None
            ),
            sasl_plain_username=settings.sasl_username,
        )
        await self._producer.start()

    async def __call__(self) -> aiokafka.AIOKafkaProducer:
        """Get the dependency (call during FastAPI request handling)."""
        if self._producer is None:
            raise RuntimeError("Dependency not initialized")
        return self._producer

    async def stop(self) -> None:
        """Stop the dependency (call during FastAPI shutdown)."""
        if self._producer is None:
            raise RuntimeError("Dependency not initialized")
        await self._producer.stop()


kafka_producer_dependency = AioKafkaProducerDependency()
