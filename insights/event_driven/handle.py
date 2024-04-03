from amqp.channel import Channel

from insights.projects.handle import (
    handle_consumers as projects_handle_consumers,
)


def handle_consumers(channel: Channel) -> None:
    projects_handle_consumers(channel)
