import amqp
from sentry_sdk import capture_exception

from insights.projects.project_dto import ProjectCreationDTO
from insights.usecases.projects.projects_use_case import ProjectsUseCase

from insights.event_driven.parsers import JSONParser
from insights.event_driven.consumer.consumers import EDAConsumer


class ProjectConsumer(EDAConsumer):  # pragma: no cover
    def consume(self, message: amqp.Message):
        print(f"[ProjectConsumer] - Consuming a message. Body: {message.body}")
        try:
            body = JSONParser.parse(message.body)

            project_dto = ProjectCreationDTO(
                uuid=body.get("uuid"),
                name=body.get("name"),
                is_template=body.get("is_template"),
                template_type_uuid=body.get("template_type_uuid"),
            )

            project_creation = ProjectsUseCase()
            project_creation.create_project(
                project_dto=project_dto, user_email=body.get("user_email")
            )

            message.channel.basic_ack(message.delivery_tag)
            print(f"[ProjectConsumer] - Project created: {project_dto.uuid}")
        except Exception as exception:
            capture_exception(exception)
            message.channel.basic_reject(message.delivery_tag, requeue=False)
            print(f"[ProjectConsumer] - Message rejected by: {exception}")
