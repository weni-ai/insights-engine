import amqp
import logging

from sentry_sdk import capture_exception

from insights.event_driven.consumers import EDAConsumer
from insights.event_driven.parsers.json_parser import JSONParser
from insights.projects.usecases.update import UpdateProjectUseCase

logger = logging.getLogger(__name__)


class UpdateProjectConsumer(EDAConsumer):
    """Consumer responsible for handling project update events from the message broker."""

    @staticmethod
    def consume(message: amqp.Message):
        """Process an incoming project update message.

        Parses the message body and delegates to ``UpdateProjectUseCase`` to
        persist changes. Acknowledges the message on success; rejects it
        without requeue on failure, logging the error and reporting it to
        Sentry.

        Args:
            message: AMQP message containing the project update payload.
                Expected keys: ``project_uuid``, ``name``, ``timezone``,
                ``date_format``, ``config``.
        """
        channel = message.channel
        print(f"[UpdateProjectConsumer] - Consuming a message. Body: {message.body}")
        body = JSONParser.parse(message.body)

        try:
            usecase = UpdateProjectUseCase()
            usecase.execute(
                project_uuid=body.get("project_uuid"),
                name=body.get("name"),
                timezone=body.get("timezone"),
                date_format=body.get("date_format"),
                config=body.get("config"),
            )
            channel.basic_ack(message.delivery_tag)
        except Exception as exception:
            channel.basic_reject(message.delivery_tag, requeue=False)
            logger.error("[UpdateProjectConsumer] - Message rejected by: %s", exception)
            capture_exception(exception)
