from rest_framework.test import APITestCase
from rest_framework.response import Response
from rest_framework import status

from insights.authentication.authentication import User
from insights.authentication.tests.decorators import with_project_auth
from insights.metrics.conversations.tests.mock import NPS_METRICS_MOCK_DATA
from insights.projects.models import Project


class BaseTestConversationsMetricsViewSet(APITestCase):
    def get_nps(self, query_params: dict) -> Response:
        url = "/v1/metrics/conversations/nps/"

        return self.client.get(url, query_params)


class TestConversationsMetricsViewSetAsAnonymousUser(
    BaseTestConversationsMetricsViewSet
):
    def test_cannot_get_nps_when_unauthenticated(self):
        response = self.get_nps({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestConversationsMetricsViewSetAsAuthenticatedUser(
    BaseTestConversationsMetricsViewSet
):
    def setUp(self) -> None:
        self.user = User.objects.create(email="test@test.com")
        self.project = Project.objects.create(name="Test Project")

        self.client.force_authenticate(self.user)

    def test_cannot_get_nps_without_project_uuid(self):
        response = self.get_nps({})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")

    def test_cannot_get_nps_without_permission(self):
        response = self.get_nps({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_cannot_get_nps_without_required_query_params(self):
        response = self.get_nps({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["start_date"][0].code, "required")
        self.assertEqual(response.data["end_date"][0].code, "required")

    @with_project_auth
    def test_get_nps(self):
        response = self.get_nps(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["score"], NPS_METRICS_MOCK_DATA["score"])
        self.assertEqual(
            response.data["total_responses"], NPS_METRICS_MOCK_DATA["total_responses"]
        )
        self.assertEqual(response.data["promoters"], NPS_METRICS_MOCK_DATA["promoters"])
        self.assertEqual(
            response.data["detractors"], NPS_METRICS_MOCK_DATA["detractors"]
        )
        self.assertEqual(response.data["passives"], NPS_METRICS_MOCK_DATA["passives"])
