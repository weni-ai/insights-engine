import uuid
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase

from insights.authentication.authentication import User
from insights.authentication.tests.decorators import with_project_auth
from insights.projects.models import Project


class BaseTestConversationsMetricsViewSet(APITestCase):
    def get_topics(self, query_params: dict) -> Response:
        url = reverse("conversations-topics")

        return self.client.get(url, query_params, format="json")

    def get_subtopics(self, query_params: dict) -> Response:
        url = reverse("conversations-subtopics")

        return self.client.get(url, query_params, format="json")

    def create_topic(self, data: dict) -> Response:
        url = reverse("conversations-topics")

        return self.client.post(url, data, format="json")

    def create_subtopic(self, data: dict) -> Response:
        url = reverse("conversations-subtopics")

        return self.client.post(url, data, format="json")


class TestConversationsMetricsViewSetAsAnonymousUser(
    BaseTestConversationsMetricsViewSet
):
    def test_cannot_get_topics_when_unauthenticated(self):
        response = self.get_topics({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_subtopics_when_unauthenticated(self):
        response = self.get_subtopics({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_create_topic_when_unauthenticated(self):
        response = self.create_topic({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_create_subtopic_when_unauthenticated(self):
        response = self.create_subtopic({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestConversationsMetricsViewSetAsAuthenticatedUser(
    BaseTestConversationsMetricsViewSet
):
    def setUp(self) -> None:
        self.user = User.objects.create(email="test@test.com")
        self.project = Project.objects.create(name="Test Project")

        self.client.force_authenticate(self.user)

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
        response = self.get_subtopics({})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")

    def test_cannot_get_subtopics_without_project_permission(self):
        response = self.get_subtopics(
            {"project_uuid": self.project.uuid, "topic_uuid": uuid.uuid4()}
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_cannot_get_subtopics_without_topic_uuid(self):
        response = self.get_subtopics({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["topic_uuid"][0].code, "required")

    @with_project_auth
    def test_get_subtopics(self):
        response = self.get_subtopics(
            {"project_uuid": self.project.uuid, "topic_uuid": uuid.uuid4()}
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
