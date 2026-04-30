from amqp.channel import Channel

from insights.settings import USE_WENI_EDA_FOR_PROJECTS

from .consumers import (
    ProjectAuthConsumer,
    OldProjectConsumer,
    UpdateProjectConsumer,
    WeniEDAProjectConsumer,
)


def handle_consumers(channel: Channel) -> None:
    if USE_WENI_EDA_FOR_PROJECTS:
        channel.basic_consume(
            "insights.projects", callback=WeniEDAProjectConsumer().handle
        )
    else:
        channel.basic_consume("insights.projects", callback=OldProjectConsumer().handle)
    channel.basic_consume("insights.permissions", callback=ProjectAuthConsumer().handle)
    channel.basic_consume(
        "insights.update-project", callback=UpdateProjectConsumer().handle
    )
