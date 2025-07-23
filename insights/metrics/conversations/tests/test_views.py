from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework.response import Response
from rest_framework import status

from insights.authentication.authentication import User
from insights.authentication.tests.decorators import with_project_auth
from insights.dashboards.models import Dashboard
from insights.metrics.conversations.enums import CsatMetricsType
from insights.metrics.conversations.services import ConversationsMetricsService
from insights.metrics.conversations.views import ConversationsMetricsViewSet
from insights.projects.models import Project
from insights.sources.flowruns.tests.mock_query_executor import (
    MockFlowRunsQueryExecutor,
)
from insights.widgets.models import Widget


class BaseTestConversationsMetricsViewSet(APITestCase):
    def get_csat_metrics(self, query_params: dict) -> Response:
        url = reverse("conversations-csat-metrics")

        return self.client.get(url, query_params, format="json")


class TestConversationsMetricsViewSetAsAnonymousUser(
    BaseTestConversationsMetricsViewSet
):
    def test_cannot_get_csat_metrics_when_unauthenticated(self):
        response = self.get_csat_metrics({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestConversationsMetricsViewSetAsAuthenticatedUser(
    BaseTestConversationsMetricsViewSet
):
    def setUp(self) -> None:
        self.user = User.objects.create(email="test@test.com")
        self.project = Project.objects.create(name="Test Project")
        self.dashboard = Dashboard.objects.create(
            name="Test Dashboard",
            project=self.project,
        )

        self.client.force_authenticate(self.user)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.original_service = ConversationsMetricsViewSet.service
        ConversationsMetricsViewSet.service = ConversationsMetricsService(
            flowruns_query_executor=MockFlowRunsQueryExecutor,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        ConversationsMetricsViewSet.service = cls.original_service

    @with_project_auth
    def test_get_csat_metrics(self):
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="flowruns",
            type="flow_result",
            position=[1, 2],
            config={
                "filter": {
                    "flow": "123",
                    "op_field": "csat",
                },
                "operation": "recurrence",
                "op_field": "result",
            },
        )

        response = self.get_csat_metrics(
            {
                "project_uuid": self.project.uuid,
                "widget_uuid": widget.uuid,
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
                "type": CsatMetricsType.HUMAN,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIsInstance(response.data["results"], list)
