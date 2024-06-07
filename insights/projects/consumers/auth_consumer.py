import amqp

from insights.event_driven.consumers import EDAConsumer
from insights.event_driven.parsers.json_parser import JSONParser
from insights.projects.usecases.auth_creation import (
    ProjectAuthCreationUseCase,
    ProjectAuthDTO,
)


class ProjectAuthConsumer(EDAConsumer):
    @staticmethod
    def consume(message: amqp.Message):
        channel = message.channel
        print(f"[ProjectAuthConsumer] - Consuming a message. Body: {message.body}")
        body = JSONParser.parse(message.body)

        try:
            project_auth_dto = ProjectAuthDTO(
                project=body.get("project"),
                user=body.get("user"),
                role=body.get("role"),
            )
            project_auth_usecase = ProjectAuthCreationUseCase()
            if body.get("action") == "delete":
                project_auth_usecase.delete_permission(project_auth_dto)
            elif body.get("action") == "create" or body.get("action") == "update":
                project_auth_usecase.create_permission(project_auth_dto)

            channel.basic_ack(message.delivery_tag)
        except Exception as exception:
            channel.basic_reject(message.delivery_tag, requeue=False)
            print(f"[ProjectConsumer] - Message rejected by: {exception}")
