from amqp.channel import Channel
from django.conf import settings

from insights.projects.consumers import WeniEDAProjectConsumer


def handle_amq_consumers(channel: Channel) -> None:
    queue_name = settings.PROJECT_AMQ_QUEUE_NAME
    channel.basic_consume(queue_name, callback=WeniEDAProjectConsumer().handle)
