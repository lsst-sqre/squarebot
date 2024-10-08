"""Configuration definition."""

from __future__ import annotations

import ssl
from enum import Enum
from pathlib import Path

from pydantic import AnyHttpUrl, DirectoryPath, Field, FilePath, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from safir.logging import LogLevel, Profile

__all__ = [
    "Configuration",
    "KafkaSecurityProtocol",
    "KafkaSaslMechanism",
    "KafkaConnectionSettings",
    "config",
]


class KafkaSecurityProtocol(str, Enum):
    """Kafka security protocols understood by aiokafka."""

    PLAINTEXT = "PLAINTEXT"
    """Plain-text connection."""

    SSL = "SSL"
    """TLS-encrypted connection."""


class KafkaSaslMechanism(str, Enum):
    """Kafka SASL mechanisms understood by aiokafka."""

    PLAIN = "PLAIN"
    """Plain-text SASL mechanism."""

    SCRAM_SHA_256 = "SCRAM-SHA-256"
    """SCRAM-SHA-256 SASL mechanism."""

    SCRAM_SHA_512 = "SCRAM-SHA-512"
    """SCRAM-SHA-512 SASL mechanism."""


class KafkaConnectionSettings(BaseSettings):
    """Settings for connecting to Kafka."""

    bootstrap_servers: str = Field(
        ...,
        title="Kafka bootstrap servers",
        description=(
            "A comma-separated list of Kafka brokers to connect to. "
            "This should be a list of hostnames or IP addresses, "
            "each optionally followed by a port number, separated by "
            "commas. "
            "For example: `kafka-1:9092,kafka-2:9092,kafka-3:9092`."
        ),
    )

    security_protocol: KafkaSecurityProtocol = Field(
        KafkaSecurityProtocol.PLAINTEXT,
        description="The security protocol to use when connecting to Kafka.",
    )

    cert_temp_dir: DirectoryPath | None = Field(
        None,
        description=(
            "Temporary writable directory for concatenating certificates."
        ),
    )

    cluster_ca_path: FilePath | None = Field(
        None,
        title="Path to CA certificate file",
        description=(
            "The path to the CA certificate file to use for verifying the "
            "broker's certificate. "
            "This is only needed if the broker's certificate is not signed "
            "by a CA trusted by the operating system."
        ),
    )

    client_ca_path: FilePath | None = Field(
        None,
        title="Path to client CA certificate file",
        description=(
            "The path to the client CA certificate file to use for "
            "authentication. "
            "This is only needed when the client certificate needs to be"
            "concatenated with the client CA certificate, which is common"
            "for Strimzi installations."
        ),
    )

    client_cert_path: FilePath | None = Field(
        None,
        title="Path to client certificate file",
        description=(
            "The path to the client certificate file to use for "
            "authentication. "
            "This is only needed if the broker is configured to require "
            "SSL client authentication."
        ),
    )

    client_key_path: FilePath | None = Field(
        None,
        title="Path to client key file",
        description=(
            "The path to the client key file to use for authentication. "
            "This is only needed if the broker is configured to require "
            "SSL client authentication."
        ),
    )

    client_key_password: SecretStr | None = Field(
        None,
        title="Password for client key file",
        description=(
            "The password to use for decrypting the client key file. "
            "This is only needed if the client key file is encrypted."
        ),
    )

    sasl_mechanism: KafkaSaslMechanism | None = Field(
        KafkaSaslMechanism.PLAIN,
        title="SASL mechanism",
        description=(
            "The SASL mechanism to use for authentication. "
            "This is only needed if SASL authentication is enabled."
        ),
    )

    sasl_username: str | None = Field(
        None,
        title="SASL username",
        description=(
            "The username to use for SASL authentication. "
            "This is only needed if SASL authentication is enabled."
        ),
    )

    sasl_password: SecretStr | None = Field(
        None,
        title="SASL password",
        description=(
            "The password to use for SASL authentication. "
            "This is only needed if SASL authentication is enabled."
        ),
    )

    model_config = SettingsConfigDict(
        env_prefix="KAFKA_", case_sensitive=False
    )

    @property
    def ssl_context(self) -> ssl.SSLContext | None:
        """An SSL context for connecting to Kafka with aiokafka, if the
        Kafka connection is configured to use SSL.
        """
        if (
            self.security_protocol != KafkaSecurityProtocol.SSL
            or self.cluster_ca_path is None
            or self.client_cert_path is None
            or self.client_key_path is None
        ):
            return None

        client_cert_path = Path(self.client_cert_path)

        if self.client_ca_path is not None:
            # Need to contatenate the client cert and CA certificates. This is
            # typical for Strimzi-based Kafka clusters.
            if self.cert_temp_dir is None:
                raise RuntimeError(
                    "KAFKIT_KAFKA_CERT_TEMP_DIR must be set when "
                    "a client CA certificate is provided."
                )
            client_ca = Path(self.client_ca_path).read_text()
            client_cert = Path(self.client_cert_path).read_text()
            sep = "" if client_ca.endswith("\n") else "\n"
            new_client_cert = sep.join([client_cert, client_ca])
            new_client_cert_path = Path(self.cert_temp_dir) / "client.crt"
            new_client_cert_path.write_text(new_client_cert)
            client_cert_path = Path(new_client_cert_path)

        # Create an SSL context on the basis that we're the client
        # authenticating the server (the Kafka broker).
        ssl_context = ssl.create_default_context(
            purpose=ssl.Purpose.SERVER_AUTH, cafile=str(self.cluster_ca_path)
        )
        # Add the certificates that the Kafka broker uses to authenticate us.
        ssl_context.load_cert_chain(
            certfile=str(client_cert_path), keyfile=str(self.client_key_path)
        )

        return ssl_context


class Configuration(BaseSettings):
    """Configuration for Squarebot."""

    name: str = Field(
        "squarebot",
        title="Name of application",
    )

    profile: Profile = Field(
        Profile.production,
        title="Application logging profile",
    )

    log_level: LogLevel = Field(
        LogLevel.INFO,
        title="Log level of the application's logger",
    )

    path_prefix: str = Field(
        "/squarebot",
        title="API URL path prefix",
        description=(
            "The URL prefix where the application's externally-accessible "
            "endpoints are hosted."
        ),
    )

    environment_url: AnyHttpUrl = Field(
        ...,
        title="Base URL of the environment",
        description=(
            "The base URL of the environment where the application is hosted."
        ),
    )

    kafka: KafkaConnectionSettings = Field(
        default_factory=KafkaConnectionSettings,
        description="Kafka connection configuration.",
    )

    app_mention_topic: str = Field(
        "squarebot.app_mention",
        title="app_mention Kafka topic",
        alias="SQUAREBOT_TOPIC_APP_MENTION",
        description="Kafka topic name for `app_mention` Slack events.",
    )

    message_channels_topic: str = Field(
        "squarebot.message.channels",
        title="message.channels Kafka topic",
        alias="SQUAREBOT_TOPIC_MESSAGE_CHANNELS",
        description=(
            "Kafka topic name for `message.channels` Slack events (messages "
            "in public channels)."
        ),
    )

    message_im_topic: str = Field(
        "squarebot.message.im",
        title="message.im Kafka topic",
        alias="SQUAREBOT_TOPIC_MESSAGE_IM",
        description=(
            "Kafka topic name for `message.im` Slack events (direct message "
            " channels)."
        ),
    )

    message_groups_topic: str = Field(
        "squarebot.message.groups",
        title="message.groups Kafka topic",
        alias="SQUAREBOT_TOPIC_MESSAGE_GROUPS",
        description=(
            "Kafka topic name for `message.groups` Slack events (messages in "
            "private channels)."
        ),
    )

    message_mpim_topic: str = Field(
        "squarebot.message.mpim",
        title="message.mpim Kafka topic",
        alias="SQUAREBOT_TOPIC_MESSAGE_MPIM",
        description=(
            "Kafka topic name for `message.mpim` Slack events (messages in "
            "multi-person direct messages)."
        ),
    )

    block_actions_topic: str = Field(
        "squarebot.interaction.block_actions",
        title="Block Actions interaction Kafka topic",
        alias="SQUAREBOT_TOPIC_BLOCK_ACTIONS",
        description=(
            "Kafka topic name for `interaction` Slack events of type "
            "`block_actions`."
        ),
    )

    view_submission_topic: str = Field(
        "squarebot.interaction.view_submission",
        title="View Submission interaction Kafka topic",
        alias="SQUAREBOT_TOPIC_VIEW_SUBMISSION",
        description=(
            "Kafka topic name for `interaction` Slack events of type "
            "`view_submission`."
        ),
    )

    # Slack signing secret
    slack_signing_secret: SecretStr = Field(
        title="Slack signing secret", alias="SQUAREBOT_SLACK_SIGNING"
    )

    slack_token: SecretStr = Field(title="Slack bot token")

    slack_app_id: str = Field(title="Slack app ID")

    model_config = SettingsConfigDict(
        env_prefix="SQUAREBOT_", case_sensitive=False
    )


config = Configuration()
"""Configuration for SQuaRE Bot."""
