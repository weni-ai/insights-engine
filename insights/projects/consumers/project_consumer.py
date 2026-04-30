from uuid import UUID
import amqp
import logging

from sentry_sdk import capture_exception

from weni.eda.django.consumers import EDAConsumer as WeniEDAConsumer

from insights.event_driven.consumers import EDAConsumer as InsightsEDAConsumer
from insights.event_driven.parsers.json_parser import JSONParser
from insights.projects.usecases.auth_creation import ProjectAuthCreationUseCase
from insights.projects.usecases.create import ProjectsUseCase
from insights.projects.usecases.project_dto import ProjectCreationDTO

logger = logging.getLogger(__name__)


def get_inline_agent_switch(body: dict) -> bool:
    """
    Handle the inline agent switch for a project.
    """
    if "inline_agent_switch" not in body or not isinstance(
        body.get("inline_agent_switch"), bool
    ):
        return True

    return body.get("inline_agent_switch")


class OldProjectConsumer(InsightsEDAConsumer):
    # TODO: Remove this consumer once we permanently migrate to Weni EDA
    @staticmethod
    def consume(message: amqp.Message):
        channel = message.channel
        print(f"[OldProjectConsumer] - Consuming a message. Body: {message.body}")
        body = JSONParser.parse(message.body)

        try:
            if body.get("organization_uuid"):
                try:
                    org_uuid = UUID(body.get("organization_uuid"))
                except ValueError as e:
                    logger.error(
                        "[OldProjectConsumer] - Invalid organization uuid: %s. Saving as None",
                        body.get("organization_uuid"),
                    )
                    capture_exception(e)
                    org_uuid = None
            else:
                org_uuid = None

            project_dto = ProjectCreationDTO(
                uuid=body.get("uuid"),
                name=body.get("name"),
                is_template=body.get("is_template"),
                date_format=body.get("date_format"),
                timezone=body.get("timezone"),
                vtex_account=body.get("vtex_account"),
                org_uuid=org_uuid,
                inline_agent_switch=get_inline_agent_switch(body),
            )

            authorizations = body.get("authorizations", [])

            project_creation = ProjectsUseCase()
            project = project_creation.create_project(project_dto)

            auth_creation = ProjectAuthCreationUseCase()
            auth_creation.bulk_create(
                project=str(project.uuid), authorizations=authorizations
            )

            channel.basic_ack(message.delivery_tag)
        except Exception as exception:
            channel.basic_reject(message.delivery_tag, requeue=False)
            print(f"[OldProjectConsumer] - Message rejected by: {exception}")


class WeniEDAProjectConsumer(WeniEDAConsumer):
    """
    Consumer responsible for handling project creation events from the Weni EDA.
    """

    def consume(self, message: amqp.Message):
        """
        Process an incoming project creation message from the Weni EDA.
        """
        channel = message.channel
        print(f"[WeniEDAProjectConsumer] - Consuming a message. Body: {message.body}")
        body = JSONParser.parse(message.body)

        try:
            if body.get("organization_uuid"):
                try:
                    org_uuid = UUID(body.get("organization_uuid"))
                except ValueError as e:
                    logger.error(
                        "[WeniEDAProjectConsumer] - Invalid organization uuid: %s. Saving as None",
                        body.get("organization_uuid"),
                    )
                    capture_exception(e)
                    org_uuid = None
            else:
                org_uuid = None

            project_dto = ProjectCreationDTO(
                uuid=body.get("uuid"),
                name=body.get("name"),
                is_template=body.get("is_template"),
                date_format=body.get("date_format"),
                timezone=body.get("timezone"),
                vtex_account=body.get("vtex_account"),
                org_uuid=org_uuid,
                inline_agent_switch=get_inline_agent_switch(body),
            )

            authorizations = body.get("authorizations", [])

            project_creation = ProjectsUseCase()
            project = project_creation.create_project(project_dto)

            auth_creation = ProjectAuthCreationUseCase()
            auth_creation.bulk_create(
                project=str(project.uuid), authorizations=authorizations
            )

            channel.basic_ack(message.delivery_tag)
        except Exception as exception:
            channel.basic_reject(message.delivery_tag, requeue=False)
            print(f"[WeniEDAProjectConsumer] - Message rejected by: {exception}")
