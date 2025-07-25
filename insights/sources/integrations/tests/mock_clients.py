import json
from uuid import UUID


from insights.sources.integrations.clients import BaseNexusClient


class MockResponse:
    def __init__(self, status_code: int, content: str):
        self.status_code = status_code
        self.content = content

    @property
    def text(self):
        return self.content

    def json(self):
        return json.loads(self.content)


class MockNexusClient(BaseNexusClient):
    """
    Mock client for Nexus API.
    """

    def get_topics(self, project_uuid: UUID) -> MockResponse:
        """
        Get conversation topics for a project.
        """

        topics = [
            {
                "name": "Cancelamento",
                "uuid": "2026cedc-67f6-4a04-977a-55cc581defa9",
                "created_at": "2025-07-15T20:56:47.582521Z",
                "description": "Quando cliente pede para cancelar um pedido",
                "subtopic": [
                    {
                        "name": "Subtopic 1",
                        "uuid": "023d2374-04ef-45b5-8b5f-5c031fafd59e",
                        "created_at": "2025-07-15T20:56:47.582521Z",
                        "description": "Quando cliente pede para cancelar um pedido",
                    },
                ],
            }
        ]

        response = MockResponse(status_code=200, content=json.dumps(topics))

        return response

    def get_subtopics(self, project_uuid: UUID, topic_uuid: UUID) -> MockResponse:
        subtopics = [
            {
                "name": "Cancelamento",
                "uuid": "2026cedc-67f6-4a04-977a-55cc581defa9",
                "created_at": "2025-07-15T20:56:47.582521Z",
                "description": "Quando cliente pede para cancelar um pedido",
                "subtopic": [],
            }
        ]
        return MockResponse(status_code=200, content=json.dumps(subtopics))

    def create_topic(
        self, project_uuid: UUID, name: str, description: str
    ) -> MockResponse:
        return MockResponse(status_code=201, content=json.dumps({}))

    def create_subtopic(
        self, project_uuid: UUID, topic_uuid: UUID, name: str, description: str
    ) -> MockResponse:
        return MockResponse(status_code=201, content=json.dumps({}))

    def delete_topic(self, project_uuid: UUID, topic_uuid: UUID) -> MockResponse:
        return MockResponse(status_code=204, content=json.dumps({}))

    def delete_subtopic(
        self, project_uuid: UUID, topic_uuid: UUID, subtopic_uuid: UUID
    ) -> MockResponse:
        return MockResponse(status_code=204, content=json.dumps({}))
