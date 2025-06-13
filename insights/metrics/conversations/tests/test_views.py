from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.response import Response

from insights.authentication.authentication import User
from insights.authentication.tests.decorators import with_project_auth
from insights.metrics.conversations.enums import ConversationsSubjectsType
from insights.metrics.conversations.tests.mock import (
    CONVERSATIONS_SUBJECTS_METRICS_MOCK_DATA,
)
from insights.projects.models import Project


class BaseTestConversationsMetricsViewSet(APITestCase):
    def get_subjects_metrics(self, query_params: dict) -> Response:
        url = "/v1/metrics/conversations/subjects/"

        return self.client.get(url, query_params)


class TestConversationsMetricsViewSetAsAnonymousUser(
    BaseTestConversationsMetricsViewSet
):
    def test_cannot_get_subjects_metrics_when_unauthenticated(self):
        response = self.get_subjects_metrics({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestConversationsMetricsViewSetAsAuthenticatedUser(
    BaseTestConversationsMetricsViewSet
):
    def setUp(self) -> None:
        self.user = User.objects.create(email="test@test.com")
        self.project = Project.objects.create(name="Test Project")

        self.client.force_authenticate(self.user)

    def test_cannot_get_subjects_metrics_without_permission(self):
        response = self.get_subjects_metrics(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "type": ConversationsSubjectsType.GENERAL,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_cannot_get_subjects_metrics_without_project_uuid(self):
        response = self.get_subjects_metrics(
            {
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "type": ConversationsSubjectsType.GENERAL,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")

    @with_project_auth
    def test_cannot_get_subjects_metrics_without_required_query_params(self):
        response = self.get_subjects_metrics(
            {
                "project_uuid": self.project.uuid,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["start_date"][0].code, "required")
        self.assertEqual(response.data["end_date"][0].code, "required")
        self.assertEqual(response.data["type"][0].code, "required")

    @with_project_auth
    def test_get_subjects_metrics(self):
        response = self.get_subjects_metrics(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "type": ConversationsSubjectsType.GENERAL,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mock_subjects_data = CONVERSATIONS_SUBJECTS_METRICS_MOCK_DATA.get(
            "subjects", []
        )

        self.assertEqual(response.data["has_more"], False)
        self.assertEqual(len(response.data["subjects"]), len(mock_subjects_data))

        for i, subject in enumerate(response.data["subjects"]):
            self.assertEqual(subject["name"], mock_subjects_data[i]["name"])
            self.assertEqual(subject["percentage"], mock_subjects_data[i]["percentage"])

    @with_project_auth
    def test_get_subjects_metrics_with_limit(self):
        mock_subjects_data = CONVERSATIONS_SUBJECTS_METRICS_MOCK_DATA.get(
            "subjects", []
        )
        response = self.get_subjects_metrics(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "type": ConversationsSubjectsType.GENERAL,
                "limit": len(mock_subjects_data) - 1,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["has_more"], True)
        self.assertEqual(len(response.data["subjects"]), len(mock_subjects_data) - 1)

        for i, subject in enumerate(response.data["subjects"]):
            self.assertEqual(subject["name"], mock_subjects_data[i]["name"])
            self.assertEqual(subject["percentage"], mock_subjects_data[i]["percentage"])
