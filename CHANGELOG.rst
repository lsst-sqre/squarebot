##########
Change log
##########

0.3.0 (2019-02-21)
==================

- SQuaRE Bot Jr now serializes the messages from user actions that are send to SQuaRE Bot Jr's Request URL.
  The supported interactions are:

  - ``block_actions`` (a user pressed a button or selected a menu item on a message)
  - ``dialog_submission`` (a user submitted a Slack dialog)
  - ``dialog_cancellation`` (a user cancelled a Slack dialog)

  Note that the Avro schema for ``block_actions`` currently only supports ``button`` and ``static_select`` actions.

- Avro schemas are now validated using the official Avro package, ``avro-python3``.

- The Kubernetes deployment includes a ``SQRBOTJR_TOKEN`` secret that other apps in api.lsst.codes can use to send messages to Slack as SQuaRE Bot Jr through Slack's Web API.

:jirap:`DM-17941`

0.2.0 (2019-02-15)
==================

This release adds the ability to serialize `message events <https://api.slack.com/events/message>`__ into Avro from the `Slack Events API <https://api.slack.com/events-api>`__ and produce Kafka messages to matching topics.

:jirap:`DM-17054`

0.1.0 (2019-01-07)
==================

This is a slack bot that will eventually replace the current SQuaRE Bot and be oriented around passing Kafka messages to downstream microservices (SQuaRE Events).
Main initial features:

- Sets up package and documentation site.
- Docker build in CI.
- Demonstrates running an `aiohttp.web <https://aiohttp.readthedocs.io/en/stable/web.html#aiohttp-web>`__ application with `structlog <http://www.structlog.org/en/stable/>`__ logging and environment-based configuration.
- Respond to the `Slack URL challenge <https://api.slack.com/events-api#subscriptions>`__).
- Implements Slack message verification based on the `signing secret <https://api.slack.com/docs/verifying-requests-from-slack`__.

:jirap:`DM-17024`
