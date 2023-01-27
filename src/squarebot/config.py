"""Configuration definition."""

from __future__ import annotations

from typing import Optional

from pydantic import AnyHttpUrl, BaseSettings, Field, FilePath, SecretStr
from safir.logging import LogLevel, Profile

__all__ = ["Configuration", "config"]


class Configuration(BaseSettings):
    """Configuration for example."""

    name: str = Field(
        "squarebot",
        title="Name of application",
        env="SAFIR_NAME",
    )

    profile: Profile = Field(
        Profile.development,
        title="Application logging profile",
        env="SAFIR_PROFILE",
    )

    log_level: LogLevel = Field(
        LogLevel.INFO,
        title="Log level of the application's logger",
        env="SAFIR_LOG_LEVEL",
    )

    path_prefix: str = Field(
        "/squarebot",
        title="API URL path prefix",
        env="SAFIR_PATH_PREFIX",
        description=(
            "The URL prefix where the application's externally-accessible "
            "endpoints are hosted."
        ),
    )

    enable_schemas: bool = Field(
        True,
        env="SQUAREBOT_ENABLE_SCHEMAS",
        description="Enable schema management, such as registering schemas.",
    )

    enable_producers: bool = Field(
        True,
        env="SQUAREBOT_ENABLE_PRODUCERS",
        description="Enable Kafka producers to backends.",
    )

    registry_url: AnyHttpUrl = Field(
        env="SQUAREBOT_REGISTRY_URL", title="Schema Registry URL"
    )

    broker_url: str = Field(
        title="Kafka broker URL", env="SQUAREBOT_BROKER_URL"
    )

    # TODO migrate to an ENUM?
    kafka_protocol: str = Field(
        title="Kafka protocol",
        env="SQUAREBOT_KAFKA_PROTOCOL",
        description="Kafka connection protocol: SSL or PLAINTEXT",
    )

    # TLS certificates for cluster + client for use with the SSL Kafka protocol
    kafka_cluster_ca_path: Optional[FilePath] = Field(
        None, title="Kafka cluster CA path", env="SQRBOTJR_KAFKA_CLUSTER_CA"
    )

    kafka_client_ca_path: Optional[FilePath] = Field(
        None, title="Kafka client CA path", env="SQUAREBOT_KAFKA_CLIENT_CA"
    )

    kafka_client_cert_path: Optional[FilePath] = Field(
        None, title="Kafka client cert path", env="SQUAREBOT_KAFKA_CLIENT_CERT"
    )

    kafka_client_key_path: Optional[FilePath] = Field(
        None, title="Kafka client key path", env="SQUAREBOT_KAFKA_CLIENT_KEY"
    )

    subject_suffix: str = Field(
        "",
        title="Schema subject name suffix",
        env="SQUAREBOT_SUBJECT_SUFFIX",
        description=(
            "Suffix to add to Schema Registry suffix names. This is useful "
            "when deploying SQuaRE Bot for testing/staging and you do not "
            "want to affect the production subject and its "
            "compatibility lineage."
        ),
    )

    # TODO convert to enum?
    subject_compatibility: str = Field(
        "FORWARD_TRANSITIVE",
        title="Schema subject compatibility",
        env="SQUAREBOT_SUBJECT_COMPATIBILITY",
        description=(
            "Compatibility level to apply to Schema Registry subjects. Use "
            "NONE for testing and development, but prefer FORWARD_TRANSITIVE "
            "for production."
        ),
    )

    app_mention_topic: str = Field(
        "squarebot.app_mention",
        title="app_mention Kafka topic",
        env="SQUAREBOT_TOPIC_APP_MENTION",
        description="Kafka topic name for `app_mention` Slack events.",
    )

    message_channels_topic: str = Field(
        "squarebot.message.channels",
        title="message.channels Kafka topic",
        env="SQUAREBOT_TOPIC_MESSAGE_CHANNELS",
        description=(
            "Kafka topic name for `message.channels` Slack events (messages "
            "in public channels)."
        ),
    )

    message_im_topic: str = Field(
        "squarebot.message.im",
        title="message.im Kafka topic",
        env="SQUAREBOT_TOPIC_MESSAGE_IM",
        description=(
            "Kafka topic name for `message.im` Slack events (direct message "
            " channels)."
        ),
    )

    message_groups_topic: str = Field(
        "squarebot.message.groups",
        title="message.groups Kafka topic",
        env="SQUAREBOT_TOPIC_MESSAGE_GROUPS",
        description=(
            "Kafka topic name for `message.groups` Slack events (messages in "
            "private channels)."
        ),
    )

    message_mpim_topic: str = Field(
        "squarebot.message.mpim",
        title="message.mpim Kafka topic",
        env="SQUAREBOT_TOPIC_MESSAGE_MPIM",
        description=(
            "Kafka topic name for `message.mpim` Slack events (messages in "
            "multi-personal direct messages)."
        ),
    )

    interaction_topic: str = Field(
        "squarebot.interaction",
        title="interaction Kafka topic",
        env="SQUAREBOT_TOPIC_INTERACTION",
        description=("Kafka topic name for `interaction` Slack events"),
    )

    # Slack signing secret
    slack_signing_secret: SecretStr = Field(
        title="Slack signing secret", env="SQUAREBOT_SLACK_SIGNING"
    )

    slack_token: SecretStr = Field(
        title="Slack bot token", env="SQUAREBOT_SLACK_TOKEN"
    )

    slack_app_id: str = Field(
        title="Slack app ID", env="SQUAREBOT_SLACK_APP_ID"
    )


config = Configuration()
"""Configuration for SQuaRE Bot."""
