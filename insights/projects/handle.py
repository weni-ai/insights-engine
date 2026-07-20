from amqp.channel import Channel
from django.conf import settings

from .consumers import (
    ProjectAuthConsumer,
    OldProjectConsumer,
    UpdateProjectConsumer,
    WeniEDAProjectConsumer,
)


def handle_consumers(channel: Channel) -> None:
    if not settings.DISABLE_OLD_PROJECT_CONSUMER:
        channel.basic_consume("insights.projects", callback=OldProjectConsumer().handle)
    channel.basic_consume("insights.permissions", callback=ProjectAuthConsumer().handle)
    channel.basic_consume(
        "insights.update-project", callback=UpdateProjectConsumer().handle
    )


def handle_consumers_amq(channel: Channel) -> None:
    if not settings.DISABLE_NEW_PROJECT_CONSUMER:
        channel.basic_consume(
            "insights.projects.queue", callback=WeniEDAProjectConsumer().handle
        )
