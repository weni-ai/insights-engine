from amqp.channel import Channel

from .consumers import (
    ProjectAuthConsumer,
    OldProjectConsumer,
    UpdateProjectConsumer,
    WeniEDAProjectConsumer,
)


def handle_consumers(channel: Channel) -> None:
    channel.basic_consume("insights.projects", callback=OldProjectConsumer().handle)
    channel.basic_consume("insights.permissions", callback=ProjectAuthConsumer().handle)
    channel.basic_consume(
        "insights.update-project", callback=UpdateProjectConsumer().handle
    )


def handle_consumers_amq(channel: Channel) -> None:
    channel.basic_consume(
        "insights.projects.queue", callback=WeniEDAProjectConsumer().handle
    )
