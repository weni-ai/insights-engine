from uuid import UUID
import amqp

from insights.event_driven.consumers import EDAConsumer
from insights.event_driven.parsers.json_parser import JSONParser
from insights.projects.usecases.auth_creation import ProjectAuthCreationUseCase
from insights.projects.usecases.create import ProjectsUseCase
from insights.projects.usecases.project_dto import ProjectCreationDTO


class ProjectConsumer(EDAConsumer):
    @staticmethod
    def consume(message: amqp.Message):
        channel = message.channel
        print(f"[ProjectConsumer] - Consuming a message. Body: {message.body}")
        body = JSONParser.parse(message.body)

        try:
            if body.get("organization_uuid"):
                try:
                    org_uuid = UUID(body.get("organization_uuid"))
                except ValueError:
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
            print(f"[ProjectConsumer] - Message rejected by: {exception}")
