##############
SQuaRE Bot, Jr
##############

SQuaRE Bot, Jr is a second-generation of SQuaRE's Slack bot that's built around SQuaRE Events, SQuaRE's Kafka pub/sub platform for api.lsst.codes.
SQuaRE Bot, Jr receives events (Slack messages, reactions, button actions, and more) from the Slack Events API and passes those on as Kafka topics in SQuaRE Events.
Other microservices in api.lsst.codes can subscribe to those topics and act on on them.
Typically those microservices will use Slack's Web API to post responses.
This architecture separates the Slack bot itself from the domain-specific concerns of user-facing SQuaRE Bot, Jr features.
You can deploy new ChatOps automations without having to update or modify SQuaRE Bot, Jr's codebase.

.. toctree::
   :maxdepth: 2

   changelog
