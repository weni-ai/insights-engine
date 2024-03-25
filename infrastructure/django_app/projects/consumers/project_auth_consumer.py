import amqp
from sentry_sdk import capture_exception

from django_app.projects.project_dto import ProjectAuthCreationDTO
from django_app.usecases.projects.create import CreateProjectAuthUseCase

from django_app.event_driven.parsers import JSONParser
from django_app.event_driven.consumer.consumers import EDAConsumer


class ProjectAuthConsumer(EDAConsumer):
    def consume(self, message: amqp.Message):
        print(f"[ProjectAuthConsumer] - Consuming a message. Body: {message.body}")
        try:
            body = JSONParser.parse(message.body)
            project_auth_dto = ProjectAuthCreationDTO(
                project_uuid=body.get("organization_uuid"),
                user_email=body.get("user_email"),
                role=body.get("role"),
            )
            project_auth_creation = CreateProjectAuthUseCase()
            project_auth_creation.create_project_auth(project_auth_dto=project_auth_dto)

            message.channel.basic_ack(message.delivery_tag)
            print(
                f"[ProjectAuthConsumer] - Project Auth created: {project_auth_dto.project_uuid}"
            )
        except Exception as exception:
            capture_exception(exception)
            message.channel.basic_reject(message.delivery_tag, requeue=False)
            print(f"[ProjectAuthConsumer] - Message rejected by: {exception}")
