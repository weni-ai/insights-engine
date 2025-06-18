from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.response import Response

from insights.authentication.authentication import User
from insights.authentication.tests.decorators import with_project_auth
from insights.metrics.conversations.tests.mock import (
    CONVERSATIONS_SUBJECTS_DISTRIBUTION_MOCK_DATA,
)
from insights.projects.models import Project


class BaseTestConversationsMetricsViewSet(APITestCase):
    def get_subjects_distribution(self, query_params: dict) -> Response:
        url = "/v1/metrics/conversations/subjects-distribution/"

        return self.client.get(url, query_params)


class TestConversationsMetricsViewSetAsAnonymousUser(
    BaseTestConversationsMetricsViewSet
):
    def test_cannot_get_subjects_distribution_when_unauthenticated(self):
        response = self.get_subjects_distribution({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestConversationsMetricsViewSetAsAuthenticatedUser(
    BaseTestConversationsMetricsViewSet
):
    def setUp(self) -> None:
        self.user = User.objects.create(email="test@test.com")
        self.project = Project.objects.create(name="Test Project")

        self.client.force_authenticate(self.user)

    def test_cannot_get_subjects_distribution_without_project_uuid(self):
        response = self.get_subjects_distribution({})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["project_uuid"][0].code,
            "required",
        )

    def test_cannot_get_subjects_distribution_without_permission(self):
        response = self.get_subjects_distribution({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_cannot_get_subjects_distribution_without_required_fields(self):
        response = self.get_subjects_distribution({"project_uuid": self.project.uuid})

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
    def test_get_subjects_distribution(self):
        response = self.get_subjects_distribution(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for group_data, group in zip(
            response.data["groups"],
            CONVERSATIONS_SUBJECTS_DISTRIBUTION_MOCK_DATA.get("groups"),
        ):
            self.assertEqual(group_data["name"], group["name"])
            self.assertEqual(group_data["percentage"], group["percentage"])
            for subject_data, subject in zip(group_data["subjects"], group["subjects"]):
                self.assertEqual(subject_data["name"], subject["name"])
                self.assertEqual(subject_data["percentage"], subject["percentage"])
