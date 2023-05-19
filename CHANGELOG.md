# Change log

<!-- scriv-insert-here -->

<a id='changelog-0.7.0'></a>

## 0.7.0 (2023-05-19)

### Backwards-incompatible changes

- sqrbot-jr is now Squarebot. It's docker image is now published at `ghcr.io/lsst-sqre/squarebot`. The app is also deployed through a Helm chart in [lsst-sqre/phalanx](https://github.com/lsst-sqre/phalanx), rather than as a Kustomize manifest. See _New features_ for more details.
- Avro schemas for messages
- Slack interaction events are currently unsupported; only Slack messages are published to Kafka.

### New features

- Squarebot is rebuilt for the modern SQuaRE app architecture: FastAPI, deployed with Helm through Phalanx.
- Squarebot uses Pydantic for modelling Avro-encoded Kafka messages. This allows for end-to-end type checking from the HTTP handlers to the messages published to Kafka.
- The `lsst-sqre/squarebot` repository is now a monorepo that contains the Squarebot service and a client library (`rubin-squarebot` on PyPI). The client library contains Pydantic models for the Avro-encoded messages published to Kafka by Squarebot. See [SQR-075](https://sqr-075.lsst.io) for details on the monorepo architecture and [SQR-076](https://sqr-076.lsst.io) background on how Pydantic is used for Kafka message modelling.

## 0.6.0 (2019-12-02)

- The event topics (for messages) have keys that contain the Slack Team ID and the channel ID. This ensures that messages in a given channel are processed sequentially.

- The interaction topics (i.e., a dialogue submission) have keys that contain the Slack Team ID and the ID of the user that triggered the interaction.

- Schemas now use the `codes.lsst.roundtable.sqrbot` namespace.

- The message schema is no longer dynamically generated with a separate wrapper schema. This significantly simplifies the loading of the message schema.

- Updated avro-python3 (a test dependency) to 1.9.1.

[DM-22408](https://jira.lsstcorp.org/browse/DM-22408)

## 0.5.0 (2019-11-29)

This release focuses on improving the deployment and configuration of SQuaRE Bot Jr.

- SQuaRE Bot Jr. can now be deployed through Kustomize.
  The base is located at `/manifests/base`.
  This means that you can incorporate this application into a specific Kustomize-based application (such as one deployed by Argo CD) with a URL such as `github.com/lsst-sqre/sqrbot-jr.git//manifests/base?ref=0.5.0`.
  There is a _separate_ template for the Secret resource expected by the deployment at `/manifests/secret.template.yaml`.

- Topics names can now be configured directly.
  See the environment variables:

  - `SQRBOTJR_TOPIC_APP_MENTION`
  - `SQRBOTJR_TOPIC_MESSAGE_CHANNELS`
  - `SQRBOTJR_TOPIC_MESSAGE_IM`
  - `SQRBOTJR_TOPIC_MESSAGE_GROUPS`
  - `SQRBOTJR_TOPIC_MESSAGE_MPIM`
  - `SQRBOTJR_TOPIC_INTERACTION`

  This granular configuration allows you to mix-and-match production and development topics.

- The old "staging version" configuration is now the `TEMPLATEBOT_SUBJECT_SUFFIX` environment variable.
  This configuration is used solely as a suffix on the fully-qualified name of a schema when determining its subject name at the Schema Registry.
  Previously it also impacted topic names.
  Use a subject suffix when trying out new Avro schemas to avoid polluting the production subject in the registry.

- SQuaRE Bot Jr can now connect to Kafka brokers through SSL.
  Set the `KAFKA_PROTOCOL` environment variable to `SSL`.
  Then set these environment variables to the paths of specific TLS certificates and keys:

  - `KAFKA_CLUSTER_CA` (the Kafka cluster's CA certificate)
  - `KAFKA_CLIENT_CA` (client CA certificate)
  - `KAFKA_CLIENT_CERT` (client certificate)
  - `KAFKA_CLIENT_KEY` (client key)

- Individual features can be enabled or disabled:

  - `SQRBOTJR_ENABLE_SCHEMAS`: set to `"0"` to disable registering new schemas on start up.
    This needs to be `1` if the producers are enabled.
  - `SQRBOTJR_ENABLE_PRODUCERS`: set to `"0"` to disable the Kafka producers.
    SQuaRE Bot Jr can still receive events from Slack though its HTTP endpoints, it just won't pass them on to Kafka.
  - `SQRBOTJR_ENABLE_TOPIC_CONFIG`: set to `"0"` to disable configuring topics if they do not already exist.
    It makes sense to disable topic configuration if a separate process is used to configure topics, such as Strimzi's TopicOperator.

[DM-22099](https://jira.lsstcorp.org/browse/DM-22099)

## 0.4.0 (2019-05-03)

There is a new configuration environment variable, `SQRBOTJR_RETENTION_MINUTES`, which configures how long a Slack messages are retained in Kafka topics.
The default is 30 minutes so that consumers can query recent history for context, but brokers will still not have too much data that could be potentially exposed.

## 0.3.1 (2019-03-15)

The `com.slack.dialog_submission_v1` schema now permits the value from a field to be `null`.
This is true if a Slack dialog field is optional and the user does not set a value.

[DM-18503](https://jira.lsstcorp.org/browse/DM-18503)

## 0.3.0 (2019-02-21)

- SQuaRE Bot Jr now serializes the messages from user actions that are send to SQuaRE Bot Jr's Request URL.
  The supported interactions are:

  - `block_actions` (a user pressed a button or selected a menu item on a message)
  - `dialog_submission` (a user submitted a Slack dialog)
  - `dialog_cancellation` (a user cancelled a Slack dialog)

  Note that the Avro schema for `block_actions` currently only supports `button` and `static_select` actions.

- Avro schemas are now validated using the official Avro package, `avro-python3`.

- The Kubernetes deployment includes a `SQRBOTJR_TOKEN` secret that other apps in api.lsst.codes can use to send messages to Slack as SQuaRE Bot Jr through Slack's Web API.

[DM-17941](https://jira.lsstcorp.org/browse/DM-17941)

## 0.2.0 (2019-02-15)

This release adds the ability to serialize [message events](https://api.slack.com/events/message) into Avro from the [Slack Events API](https://api.slack.com/events-api) and produce Kafka messages to matching topics.

[DM-17054](https://jira.lsstcorp.org/browse/DM-17054)

## 0.1.0 (2019-01-07)

This is a slack bot that will eventually replace the current SQuaRE Bot and be oriented around passing Kafka messages to downstream microservices (SQuaRE Events).
Main initial features:

- Sets up package and documentation site.
- Docker build in CI.
- Demonstrates running an [aiohttp.web](https://aiohttp.readthedocs.io/en/stable/web.html#aiohttp-web) application with [structlog](http://www.structlog.org/en/stable/) logging and environment-based configuration.
- Respond to the [Slack URL challenge](https://api.slack.com/events-api#subscriptions).
- Implements Slack message verification based on the [signing secret](https://api.slack.com/docs/verifying-requests-from-slack).

[DM-17024](https://jira.lsstcorp.org/browse/DM-17024)
