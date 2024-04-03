from amqp.channel import Channel

from .consumers import DeadLetterConsumer, ProjectConsumer


def handle_consumers(channel: Channel) -> None:
    channel.basic_consume("insights.projects", callback=ProjectConsumer().handle)
    channel.basic_consume("insights.dlq", callback=DeadLetterConsumer.consume)
