from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase

from insights.authentication.authentication import User
from insights.projects.models import Project


class BaseTestConversationsMetricsViewSet(APITestCase):
    def get_timeseries(self, query_params: dict) -> Response:
        url = "/v1/metrics/conversations/timeseries/"

        return self.client.get(url, query_params)


class TestConversationsMetricsViewSetAsAnonymousUser(
    BaseTestConversationsMetricsViewSet
):
    def test_cannot_get_timeseries_when_unauthenticated(self) -> None:
        response = self.get_timeseries({})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestConversationsMetricsViewSetAsAuthenticatedUser(
    BaseTestConversationsMetricsViewSet
):
    def setUp(self) -> None:
        self.user = User.objects.create(email="test@test.com")
        self.project = Project.objects.create(name="Test Project")

        self.client.force_authenticate(self.user)
