"""The FastStream Kafka router for SQuaRE Bot."""

from __future__ import annotations

from faststream.kafka.fastapi import KafkaRouter
from faststream.security import BaseSecurity

from .config import config

__all__ = ["kafka_router"]


kafka_security = BaseSecurity(ssl_context=config.kafka.ssl_context)
kafka_router = KafkaRouter(
    config.kafka.bootstrap_servers, security=kafka_security
)
