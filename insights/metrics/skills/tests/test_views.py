from unittest.mock import patch

from django.utils import timezone
from django.utils.timezone import timedelta
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.response import Response

from insights.authentication.authentication import User
from insights.authentication.tests.decorators import (
    with_internal_auth,
    with_project_auth,
)
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

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")

    def test_cannot_get_metrics_for_skill_without_project_permission(self):
        response = self.get_metrics_for_skill({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_cannot_get_metrics_without_skill_name(self):
        response = self.get_metrics_for_skill({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["skill"][0].code, "required")

    @with_project_auth
    def test_cannot_get_metrics_with_invalid_skill_name(self):
        invalid_skill_name = "example"

        response = self.get_metrics_for_skill(
            {"project_uuid": self.project.uuid, "skill": invalid_skill_name}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"], f"Invalid skill name: {invalid_skill_name}"
        )

    @with_project_auth
    def test_cannot_get_metrics_for_the_abandoned_cart_skill_without_dates(self):
        response = self.get_metrics_for_skill(
            {"project_uuid": self.project.uuid, "skill": "abandoned_cart"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"], "Missing required fields: start_date, end_date"
        )

    @with_project_auth
    @patch(
        "insights.metrics.skills.services.abandoned_cart.AbandonedCartSkillService.get_metrics"
    )
    def test_get_metrics_for_the_abandoned_cart_skill(self, mock_metrics):
        expected_metrics = [
            {
                "id": "sent-messages",
                "value": 50,
            },
            {
                "id": "delivered-messages",
                "value": 45,
            },
            {
                "id": "read-messages",
                "value": 40,
            },
            {
                "id": "interactions",
                "value": 35,
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
                "start_date": (timezone.now() - timedelta(days=7)).date(),
                "end_date": timezone.now().date(),
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestSkillsMetricsViewAsInternalUser(BaseTestSkillsMetrisView):
    def setUp(self) -> None:
        self.user = User.objects.create_user(email="test@mail.com")
        self.project = Project.objects.create()

        self.client.force_authenticate(self.user)

    @with_internal_auth
    @patch(
        "insights.metrics.skills.services.abandoned_cart.AbandonedCartSkillService.get_metrics"
    )
    def test_can_get_metrics_for_skill(self, mock_metrics):
        mock_metrics.return_value = {}

        response = self.get_metrics_for_skill(
            {
                "project_uuid": self.project.uuid,
                "skill": "abandoned_cart",
                "start_date": (timezone.now() - timedelta(days=7)).date(),
                "end_date": timezone.now().date(),
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cannot_get_metrics_for_skill_without_internal_permission(self):
        response = self.get_metrics_for_skill({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
