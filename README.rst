##########
SQuaRE Bot
##########

SQuaRE Bot is a SQuaRE's Slack bot that's built around Kafka-based backends for processing and responding to messages.
SQuaRE Bot, Jr receives events (Slack messages, reactions, button actions, and more) from the Slack Events API and passes those on as messages in Kafka topics.
Other microservices Roundtable can subscribe to those topics and act on on them.
Typically those microservices will use Slack's Web API to post responses.
This architecture separates the Slack bot itself from the domain-specific concerns of user-facing SQuaRE Bot features.
You can deploy new ChatOps automations without having to update or modify SQuaRE Bot's codebase.
