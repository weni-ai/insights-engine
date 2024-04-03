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
        print(
            f"[ProjectPermissionConsumer] - Consuming a message. Body: {message.body}"
        )
        body = JSONParser.parse(message.body)

        project_auth_dto = ProjectAuthDTO(
            project=body.get("project"),
            user=body.get("user"),
            role=body.get("role"),
        )
        project_auth_usecase = ProjectAuthCreationUseCase()
        project_auth_usecase_action_method = getattr(
            project_auth_usecase, body.get("action")
        )
        project_auth_usecase_action_method(project_auth_dto)

        channel.basic_ack(message.delivery_tag)
