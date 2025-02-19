from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.response import Response

from insights.authentication.authentication import User
from insights.authentication.tests.decorators import with_project_auth
from insights.projects.models import Project


class BaseTestSkillsMetrisView(APITestCase):
    def get_metrics_for_skill(self, filters: dict) -> Response:
        url = "/v1/metrics/skills/"

        return self.client.get(url, filters)


class TestSkillsMetricsViewAsAnonymousUser(BaseTestSkillsMetrisView):
    def test_cannot_get_metrics_for_skill_when_unauthenticated(self):
        response = self.get_metrics_for_skill({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestSkillsMetricsViewAsAuthenticatedUser(BaseTestSkillsMetrisView):
    def setUp(self) -> None:
        self.user = User.objects.create_user(email="test@mail.com")
        self.project = Project.objects.create()

        self.client.force_authenticate(self.user)

    def test_cannot_get_metrics_for_skill_without_project_uuid(self):
        response = self.get_metrics_for_skill({})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_cannot_get_metrics_for_skill_without_required_fields(self):
        response = self.get_metrics_for_skill({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @with_project_auth
    @patch(
        "insights.metrics.skills.services.abandoned_cart.AbandonedCartService.get_metrics"
    )
    def test_get_metrics_for_the_abandoned_cart_skill(self, mock_metrics):
        expected_metrics = [
            {
                "id": "sent-messages",
                "value": 50,
                "percentage": 100.0,
            },
            {
                "id": "delivered-messages",
                "value": 45,
                "percentage": 125.0,
            },
            {
                "id": "read-messages",
                "value": 40,
                "percentage": 166.67,
            },
            {
                "id": "interactions",
                "value": 35,
                "percentage": 250,
            },
            {
                "id": "utm-revenue",
                "value": 5000,
                "percentage": 0,
                "prefix": "R$",
            },
            {
                "id": "orders-placed",
                "value": 200,
                "percentage": 0,
            },
        ]
        mock_metrics.return_value = expected_metrics

        response = self.get_metrics_for_skill(
            {
                "project_uuid": self.project.uuid,
                "skill": "abandoned_cart",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
