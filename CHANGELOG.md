# Change log

<!-- scriv-insert-here -->

<a id='changelog-0.10.0'></a>

## 0.10.0 (2024-09-26)

### Backwards-incompatible changes

- `SquarebotSlackMessageValue.user` is now nullable. It will be `null` if the message is a `bot_message` subtype.

### New features

- Added `SquarebotSlackMessageValue.bot_id` to capture the ID of the app that send a bot message.

- Support for Slack [block actions](https://api.slack.com/reference/interaction-payloads/block-actions) interactions. These interactions happen when a user interacts with a message's interactive elements (e.g., buttons, menus). These Slack payloads are parsed into `SlackBlockActionsPayload` objects and published to a block action Kafka topic (`$SQUAREBOT_TOPIC_BLOCK_ACTIONS`) with `SquarebotSlackBlockActionsKey` key and `SquarebotSlackBlockActionsValue` value models.

- Support for Slack [view submission](https://api.slack.com/reference/interaction-payloads/views) interactions. These interactions happen when a modal is submitted. These Slack payloads are parsed into `SlackViewSubmissionPayload` objects and published to a view submission Kafka topic (`$SQUAREBOT_TOPIC_VIEW_SUBMISSION`) with `SquarebotSlackViewSubmissionKey` key and `SquarebotSlackViewSubmissionValue` value models. The value model doesn't yet fully parse the view into Pydantic models; clients will need to inspect the JSON object to get the submitted state of the model. Once more Pydantic modeling of Slack views and Block Kit blocks and elements is implemented, we can update the value model to provide more fully typed messages.

- Publish AsyncAPI documentation to the `/asyncapi` endpoint. This documentation site is generated automatically through Faststream.

### Bug fixes

- Fix setting the `is_bot` property of `SquarebotSlackMessageValue` to account for messages without the `bot_message` subtype, but which still have a `bot_id` set.

- Improved the Slack message verification so that it now handles both JSON-formatted posts and url-encoded form posts. This change is necessary because Slack sends JSON-formatted posts for messages and url-encoded form posts for interactions. The verification now works for both types of posts.

<a id='changelog-0.9.0'></a>

## 0.9.0 (2024-07-25)

### Backwards-incompatible changes

- `SquarebotSlackMessageValue` no longer includes a `bot_id` field. Instead, the `user` field is set to the bot's ID and a new `is_bot` field indicates if the `user` field is a bot or user ID.

### New features

- Add support for Slack messages with `subtype` of `bot_message`. This is implemented in the Slack message model `SlackMessageEventContent` as a new `subtype` field that now takes a `SlackMessageSubtype` enum. The Kafka representation of this message, `SquarebotSlackMessageValue` has been updated to now set the `user` attribute to either the user's ID or the bot's ID as appropriate. A new flag, `is_bot` indicates if the `user` field reflects a user or bot (app integration) identifier.

- `SlackMessageEventContent`, a part of the `SlackkMessageEvent` model, now has support for `attachments`. Slack attachments are deprecated for Block Kit, but are still widely used by app integrations. The `attachments` field is a list of `SlackMessageAttachment` objects. These attachments can have text content or individual fields that have titles and values.

- The `SquarebotSlackMessageValue` Kafka message model's `text` field now includes the combined content of the message and its attachments. This makes it easy for consumers to process message content without needing to check for attachments and Block Kit fields. For consumers that _are_ sensitive to the exact structure of the message, the `slack_event` field is still available, which is the original JSON representation of the Slack message, which can be parsed into a `SlackMessageEvent` object.

### Other changes

- Adopt `ruff-shared.toml` from https://github.com/lsst/templates

- The noxfile now uses `uv` as the backend for pip and pip-compile tasks.

- Added a new weekly GitHub Actions CI workflow to validate that the app will run with future versions of dependencies.

<a id='changelog-0.8.0'></a>

## 0.8.0 (2024-02-28)

### Backwards-incompatible changes

- Squarebot now publishes messages in JSON, rather than Avro. Consumers should use the Pydantic models published in the `rubin-squarebot` PyPI package to deserialize messages.

- The `rubin-squarebot` PyPI package now uses the `rubin.squarebot` Python namespace (previously `rubinobs.square.squarebot`). Consumers should use the `rubin.squarebot.models.kafka.SquarebotSlackMessageValue` Pydantic model to deserialize Squarebot messages for Slack channel message traffic (or `rubin.squarebot.models.kafka.SquarebotSlackMessageValue` for the app mention topic).

- The codebase now uses Pydantic 2.

### New features

- Squarebot now uses [FastStream](https://faststream.airt.ai/) to publish messages. This approach drops the Confluent Schema Registry integration because messages are now published in JSON from Pydantic models, and those Pydantic models are versioned and published through the `rubin-squarebot` PyPI package.

- New fields in the `SquarebotSlackMessageValue` Pydantic model:

  - `thread_ts`, useful for identify a threaded message and replying to its thread.
  - `bot_id`, the ID of the bot that sent the message (if applicable). This is useful for identifying bot messages and ignoring them in some cases.

### Bug fixes

- Fix type annotations related in `channel_type` in `rubin.squarebot.models.kafka.SquarebotSlackMessageValue`. We now assure that the channel type is not Null here. However the `channel_type` field is now set to null/None in the `SquarebotSlackAppMentionValue` model.

- Fixed the `nox -s init` command so that it will install into the current Python environment (previously it still installing into the environment managed by `nox`).

### Other changes

- A Redoc-based OpenAPI documentation page for the REST API is now included in the Sphinx documentation.

- Switched to [nox](https://nox.thea.codes/en/stable/) for running tests and repository tasks. Nox now replaces the two tox configurations for the client and server. Nox also replaces the `Makefile` for repository tasks:
  - `nox -s venv-init` initializes a Python venv virtual environment and installs the application into it. Alternatively, `nox -s init` can be used to initialize the application in the current Python environment (like `make init`).
  - `nox -s update-deps` updates the pinned dependencies as well as the pre-commit hooks (replacing `make update-deps`).
- New nox integration with scriv for change log management: `nox -s scriv-create` creates a change log fragment and `nox -s scriv-collect X.Y.Z` collects change log fragments into CHANGELOG.md for a release.

- Adopt the lsst-sqre/build-and-push-to-ghcr@v1 action.

- Tests require a local Kafka broker. The easiest way to run a Kafka broker is with Docker Compose and the `kafka-compose.yaml` configuration file in this repository. The Docker compose set up also deploys Kafdrop so you can view the messages produced during testing.

- The codebase is now linted and formatted with Ruff.

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
