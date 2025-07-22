import uuid
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.response import Response

from insights.authentication.authentication import User
from insights.authentication.tests.decorators import with_project_auth
from insights.metrics.conversations.enums import ConversationType
from insights.metrics.conversations.integrations.datalake.tests.mock_services import (
    MockDatalakeConversationsMetricsService,
)
from insights.metrics.conversations.services import ConversationsMetricsService
from insights.metrics.conversations.views import ConversationsMetricsViewSet
from insights.projects.models import Project
from insights.sources.integrations.tests.mock_clients import MockNexusClient


class BaseTestConversationsMetricsViewSet(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.original_service = ConversationsMetricsViewSet.service
        ConversationsMetricsViewSet.service = ConversationsMetricsService(
            datalake_service=MockDatalakeConversationsMetricsService(),
            nexus_client=MockNexusClient(),
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        ConversationsMetricsViewSet.service = cls.original_service

    def get_topics_distribution(self, query_params: dict) -> Response:
        url = "/v1/metrics/conversations/topics-distribution/"

        return self.client.get(url, query_params)

    def get_topics(self, query_params: dict) -> Response:
        url = reverse("conversations-topics")

        return self.client.get(url, query_params, format="json")

    def get_subtopics(self, topic_uuid: uuid.UUID, query_params: dict) -> Response:
        url = reverse("conversations-subtopics", kwargs={"topic_uuid": topic_uuid})

        return self.client.get(url, query_params, format="json")

    def create_topic(self, data: dict) -> Response:
        url = reverse("conversations-topics")

        return self.client.post(url, data, format="json")

    def create_subtopic(self, topic_uuid: uuid.UUID, data: dict) -> Response:
        url = reverse("conversations-subtopics", kwargs={"topic_uuid": topic_uuid})

        return self.client.post(url, data, format="json")

    def delete_topic(self, topic_uuid: uuid.UUID, data: dict) -> Response:
        url = reverse("conversations-topic", kwargs={"topic_uuid": topic_uuid})

        return self.client.delete(url, data, format="json")

    def delete_subtopic(
        self, topic_uuid: uuid.UUID, subtopic_uuid: uuid.UUID, data: dict
    ) -> Response:
        url = reverse(
            "conversations-subtopic",
            kwargs={"topic_uuid": topic_uuid, "subtopic_uuid": subtopic_uuid},
        )

        return self.client.delete(url, data, format="json")


class TestConversationsMetricsViewSetAsAnonymousUser(
    BaseTestConversationsMetricsViewSet
):
    def test_cannot_get_topics_distribution_when_unauthenticated(self):
        response = self.get_topics_distribution({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_topics_when_unauthenticated(self):
        response = self.get_topics({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_subtopics_when_unauthenticated(self):
        response = self.get_subtopics(uuid.uuid4(), {})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_create_topic_when_unauthenticated(self):
        response = self.create_topic({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_create_subtopic_when_unauthenticated(self):
        response = self.create_subtopic(uuid.uuid4(), {})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_delete_topic_when_unauthenticated(self):
        response = self.delete_topic(uuid.uuid4(), {})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_delete_subtopic_when_unauthenticated(self):
        response = self.delete_subtopic(uuid.uuid4(), uuid.uuid4(), {})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestConversationsMetricsViewSetAsAuthenticatedUser(
    BaseTestConversationsMetricsViewSet
):
    def setUp(self) -> None:
        self.user = User.objects.create(email="test@test.com")
        self.project = Project.objects.create(name="Test Project")  # type: ignore

        self.client.force_authenticate(self.user)

    def test_cannot_get_topics_distribution_without_project_uuid(self):
        response = self.get_topics_distribution({})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["project_uuid"][0].code,
            "required",
        )

    def test_cannot_get_topics_distribution_without_permission(self):
        response = self.get_topics_distribution({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_cannot_get_topics_distribution_without_required_fields(self):
        response = self.get_topics_distribution({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["start_date"][0].code,
            "required",
        )
        self.assertEqual(
            response.data["end_date"][0].code,
            "required",
        )

    @with_project_auth
    def test_get_topics_distribution(self):
        response = self.get_topics_distribution(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "type": ConversationType.AI,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn("topics", response.data)
        self.assertIn("uuid", response.data["topics"][0])
        self.assertIn("name", response.data["topics"][0])
        self.assertIn("quantity", response.data["topics"][0])
        self.assertIn("subtopics", response.data["topics"][0])
        self.assertIn("percentage", response.data["topics"][0])

    def test_cannot_get_topics_without_project_uuid(self):
        response = self.get_topics({})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")

    def test_cannot_get_topics_without_project_permission(self):
        response = self.get_topics({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_get_topics(self):
        response = self.get_topics({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cannot_get_subtopics_without_project_uuid(self):
        response = self.get_subtopics(uuid.uuid4(), {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")

    def test_cannot_get_subtopics_without_project_permission(self):
        response = self.get_subtopics(uuid.uuid4(), {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_get_subtopics(self):
        topic_uuid = uuid.uuid4()

        response = self.get_subtopics(
            topic_uuid,
            {"project_uuid": self.project.uuid},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @with_project_auth
    def test_cannot_create_topic_without_required_fields(self):
        response = self.create_topic({})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")
        self.assertEqual(response.data["name"][0].code, "required")
        self.assertEqual(response.data["description"][0].code, "required")

    @with_project_auth
    def test_create_topic(self):
        response = self.create_topic(
            {
                "project_uuid": self.project.uuid,
                "name": "Test Topic",
                "description": "Test Description",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cannot_create_subtopic_without_project_permission(self):
        response = self.create_subtopic(
            uuid.uuid4(),
            {
                "project_uuid": self.project.uuid,
                "name": "Test Subtopic",
                "description": "Test Subtopic Description",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_create_subtopic_without_required_fields(self):
        response = self.create_topic({})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")
        self.assertEqual(response.data["name"][0].code, "required")
        self.assertEqual(response.data["description"][0].code, "required")

    @with_project_auth
    def test_create_subtopic(self):
        topic_uuid = uuid.uuid4()
        response = self.create_subtopic(
            topic_uuid,
            {
                "project_uuid": self.project.uuid,
                "name": "Test Subtopic",
                "description": "Test Subtopic Description",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cannot_delete_topic_without_project_uuid(self):
        response = self.delete_topic(uuid.uuid4(), {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")

    def test_cannot_delete_topic_without_project_permission(self):
        response = self.delete_topic(uuid.uuid4(), {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_delete_topic(self):
        response = self.delete_topic(uuid.uuid4(), {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_cannot_delete_subtopic_without_project_uuid(self):
        response = self.delete_subtopic(uuid.uuid4(), uuid.uuid4(), {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")

    def test_cannot_delete_subtopic_without_project_permission(self):
        response = self.delete_subtopic(
            uuid.uuid4(), uuid.uuid4(), {"project_uuid": self.project.uuid}
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_delete_subtopic(self):
        response = self.delete_subtopic(
            uuid.uuid4(), uuid.uuid4(), {"project_uuid": self.project.uuid}
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
