# Squarebot

Squarebot is the nexus service for ChatOps and event-driven bots for Rubin Observatory.
As a Slack app, Squarebot receives events from Slack and publishes them into specific _Square Events_ Kafka topics in the [Roundtable Kubernetes cluster](https://phalanx.lsst.io/environments/roundtable-prod/index.html).
Other applications on Roundtable can consume these events and act on them, such as by posting messages back to Slack or by performing some other background automation.

```mermaid
flowchart LR
    subgraph Slack
    message[Slack message]
    interaction[Slack interaction]
    end
    subgraph sqrbot ["Squarebot"]
    eventapi["/slack/event"]
    interactionapi["/slack/interaction"]
    message -->|HTTP POST| eventapi
    interaction -->|HTTP POST| interactionapi
    end
    subgraph kafka ["Kafka Topics"]
    topicmention["lsst.square-events.squarebot.slack.app.mention"]
    topicchannel["lsst.square-events.squarebot.slack.message.channel"]
    topicgroup["lsst.square-events.squarebot.slack.message.group"]
    topicim["lsst.square-events.squarebot.slack.message.im"]
    topicmpim["lsst.square-events.squarebot.slack.message.mpim"]
    topicinteraction["lsst.square-events.squarebot.slack.interaction"]
    end
    eventapi --> topicmention
    eventapi --> topicchannel
    eventapi --> topicgroup
    eventapi --> topicim
    eventapi --> topicmpim
    interactionapi --> topicinteraction
    subgraph backends ["Backends"]
    backend1["Backend 1"]
    backend2["Backend 2"]
    end
    topicchannel --> backend1
    topicgroup --> backend1
    topicmention --> backend2
    topicinteraction --> backend2
```

Slack integration is implemented at the time.
We plan to add support for other event sources, such as GitHub, in the future.

Squarebot is built on top of [FastAPI](https://fastapi.tiangolo.com/), a modern Python web framework, with Rubin/SQuaRE libraries [Safir](https://safir.lsst.io) (FastAPI application libraries) and [Kafkit](https://kafkit.lsst.io) (Kafka integration).
