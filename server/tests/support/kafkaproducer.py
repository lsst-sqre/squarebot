"""Mock PydanticKafkaProducer for testing."""

from collections.abc import Iterator
from unittest.mock import AsyncMock, Mock, patch


def patch_aiokafkaproducer() -> Iterator[Mock]:
    with patch("aiokafka.AIOKafkaProducer", autospec=True) as mock_producer:
        mock_producer.start = AsyncMock(return_value=None)
        mock_producer.stop = AsyncMock(return_value=None)
        mock_producer.send = AsyncMock(return_value=None)
        yield mock_producer
