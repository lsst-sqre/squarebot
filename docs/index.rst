##########
SQuaRE Bot
##########

SQuaRE Bot is the third-generation of SQuaRE's distributed Slack bot for Rubin Observatory.

SQuaRE Bot receives events (Slack messages, reactions, button actions, and more) from the Slack event and interaction APIs and passes those on as messages in corresponding Kafka topics published within the Roundtable platform.
Other microservices in Roundtable can subscribe to those topics and act on on them.
Typically those microservices will use Slack's Web API to post responses.
This architecture separates the Slack bot itself from the domain-specific concerns of user-facing SQuaRE Bot features.
You can deploy new ChatOps automations without having to update or modify SQuaRE Bot's codebase.

.. toctree::
   :hidden:

   changelog
