import logging
from uuid import UUID

import amqp
from sentry_sdk import capture_exception
from weni.eda.django.consumers import EDAConsumer as WeniEDAConsumer
from weni.eda.messages import Message

from insights.event_driven.consumers import EDAConsumer as InsightsEDAConsumer
from insights.event_driven.parsers.json_parser import JSONParser
from insights.projects.usecases.auth_creation import ProjectAuthCreationUseCase
from insights.projects.usecases.create import ProjectsUseCase
from insights.projects.usecases.project_dto import ProjectCreationDTO

logger = logging.getLogger(__name__)

EVENT_TYPE_PROJECT_CREATED = "project.created"


def get_inline_agent_switch(body: dict) -> bool:
    """
    Handle the inline agent switch for a project.
    """
    if "inline_agent_switch" not in body or not isinstance(
        body.get("inline_agent_switch"), bool
    ):
        return True

    return body.get("inline_agent_switch")


def _parse_org_uuid(organization_uuid, consumer_name: str) -> UUID | None:
    if not organization_uuid:
        return None

    try:
        return UUID(str(organization_uuid))
    except ValueError as e:
        logger.error(
            "[%s] - Invalid organization uuid: %s. Saving as None",
            consumer_name,
            organization_uuid,
        )
        capture_exception(e)
        return None


def _normalize_vtex_account(value) -> str | None:
    if isinstance(value, str):
        return value.strip() or None
    return value


class OldProjectConsumer(InsightsEDAConsumer):
    # TODO: Remove this consumer once we permanently migrate to Weni EDA
    @staticmethod
    def consume(message: amqp.Message):
        channel = message.channel
        print(f"[OldProjectConsumer] - Consuming a message. Body: {message.body}")
        body = JSONParser.parse(message.body)

        try:
            org_uuid = _parse_org_uuid(
                body.get("organization_uuid"), "OldProjectConsumer"
            )

            project_dto = ProjectCreationDTO(
                uuid=body.get("uuid"),
                name=body.get("name"),
                is_template=body.get("is_template"),
                date_format=body.get("date_format"),
                timezone=body.get("timezone"),
                vtex_account=_normalize_vtex_account(body.get("vtex_account")),
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
    """Consume project creation events from insights.projects.queue.

    Messages use the weni-eda Event envelope and are routed by event_type.
    """

    def __init__(self):
        self.create_usecase = ProjectsUseCase()
        self.auth_creation_usecase = ProjectAuthCreationUseCase()

    def consume(self, message: Message):
        event = message.event()
        data = event.data or {}

        if event.event_type == EVENT_TYPE_PROJECT_CREATED:
            self._handle_project_created(data)
        else:
            raise ValueError(f"Unsupported event_type: {event.event_type}")

        self.ack()
        logger.info("Successfully processed %s", event.event_type)

    def _handle_project_created(self, data: dict) -> None:
        project_uuid = data.get("uuid")
        if not project_uuid:
            raise ValueError("Missing required fields for project created event")

        org_uuid = _parse_org_uuid(
            data.get("organization_uuid"), "WeniEDAProjectConsumer"
        )

        project_dto = ProjectCreationDTO(
            uuid=project_uuid,
            name=data.get("name"),
            is_template=data.get("is_template"),
            date_format=data.get("date_format"),
            timezone=data.get("timezone", "UTC"),
            vtex_account=_normalize_vtex_account(data.get("vtex_account")),
            org_uuid=org_uuid,
            inline_agent_switch=get_inline_agent_switch(data),
        )

        authorizations = data.get("authorizations", [])

        project = self.create_usecase.create_project(project_dto)
        self.auth_creation_usecase.bulk_create(
            project=str(project.uuid), authorizations=authorizations
        )
