"""Kafka producer service that accepts with Pydantic models."""

from __future__ import annotations

from asyncio import Future
from typing import Optional

from aiokafka import AIOKafkaProducer
from dataclasses_avroschema.avrodantic import AvroBaseModel
from kafkit.registry.manager import PydanticSchemaManager


class PydanticKafkaProducer:
    """Kafka producer that sends Pydantic models for message values and keys,
    built around aiokafka.

    Parameters
    ----------
    producer
        The aiokafka producer.
    schema_manager
        The Pydantic schema manager used by the Pydantic Kafka producer.
    """

    def __init__(
        self, producer: AIOKafkaProducer, schema_manager: PydanticSchemaManager
    ) -> None:
        self._producer = producer
        self._schema_manager = schema_manager

    @property
    def aiokafka_producer(self) -> AIOKafkaProducer:
        """The aiokafka producer (access-only)."""
        return self._producer

    @property
    def schema_manager(self) -> PydanticSchemaManager:
        """The Pydantic schema manager used by the Pydantic Kafka
        producer (access-only).
        """
        return self._schema_manager

    async def send(
        self,
        *,
        topic: str,
        value: AvroBaseModel,
        key: Optional[AvroBaseModel] = None,
        partition: Optional[None] = None,
        timestamp_ms: Optional[int] = None,
        headers: Optional[dict[str, bytes]] = None,
    ) -> Future:
        """Send a message to a Kafka topic.

        Parameters
        ----------
        topic
            The topic to send the message to.
        value
            The message value.
        key
            The message key.
        partition
            The partition to send the message to.
        timestamp_ms
            The timestamp of the message.
        headers
            The headers of the message.

        Returns
        -------
        asyncio.Future
            A future that resolves when the message is sent.
        """
        serialized_value = await self._schema_manager.serialize(value)
        if key:
            serialized_key = await self._schema_manager.serialize(key)
        else:
            serialized_key = None

        return await self._producer.send(
            topic,
            value=serialized_value,
            key=serialized_key,
            partition=partition,
            timestamp_ms=timestamp_ms,
            headers=headers,
        )
