"""The FastStream Kafka broker for SQuaRE Bot."""

from __future__ import annotations

from faststream.kafka import KafkaBroker
from faststream.security import BaseSecurity

from .config import config

__all__ = ["kafka_broker"]


# Hand-rolled BaseSecurity wiring is kept as-is here (not normalized to
# safir.kafka.KafkaConnectionSettings) because squarebot's own
# KafkaConnectionSettings (config.py) exposes ``cert_temp_dir``,
# ``client_ca_path``, and ``client_key_password`` fields/env vars for
# Strimzi-style client-cert concatenation that safir's version does not
# have, and safir's settings model uses ``extra="forbid"``. Adopting it
# could silently drop support for those env vars if Phalanx ever sets them.
kafka_security = BaseSecurity(ssl_context=config.kafka.ssl_context)
kafka_broker = KafkaBroker(
    config.kafka.bootstrap_servers,
    security=kafka_security,
)
