from unittest.mock import MagicMock
import uuid
from rest_framework.test import APITestCase
from rest_framework.response import Response
from rest_framework import status

from insights.authentication.tests.decorators import with_project_auth
from insights.dashboards.models import Dashboard
from insights.metrics.conversations.api.v2.views import ConversationsMetricsViewSetV2
from insights.metrics.conversations.enums import NpsMetricsType
from insights.metrics.conversations.integrations.datalake.services import (
    BaseConversationsMetricsService,
)
from insights.metrics.conversations.services import (
    ConversationsMetricsService,
)
from insights.projects.models import Project
from insights.sources.integrations.clients import BaseNexusClient
from insights.users.models.user import User
from insights.widgets.models import Widget
from insights.sources.flowruns.tests.mock_query_executor import (
    MockFlowRunsQueryExecutor,
)


class BaseTestConversationsMetricsViewSetV2(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.original_service = ConversationsMetricsViewSetV2.service
        ConversationsMetricsViewSetV2.service = ConversationsMetricsService(
            datalake_service=MagicMock(spec=BaseConversationsMetricsService),
            nexus_client=MagicMock(spec=BaseNexusClient),
            flowruns_query_executor=MockFlowRunsQueryExecutor,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        ConversationsMetricsViewSetV2.service = cls.original_service

    def get_nps_metrics(self, query_params: dict) -> Response:
        url = "/v2/metrics/conversations/nps/"

        return self.client.get(url, query_params)


class TestConversationsMetricsViewSetV2AsAnonymousUser(
    BaseTestConversationsMetricsViewSetV2
):
    def test_cannot_get_nps_metrics_when_unauthenticated(self):
        response = self.get_nps_metrics({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestConversationsMetricsViewSetV2AsAuthenticatedUser(
    BaseTestConversationsMetricsViewSetV2
):
    def setUp(self):
        self.user = User.objects.create(email="test@test.com")
        self.project = Project.objects.create(name="Test Project")
        self.dashboard = Dashboard.objects.create(
            name="Test Dashboard",
            project=self.project,
        )

        self.client.force_authenticate(self.user)

    def test_cannot_get_nps_metrics_without_project_uuid(self):
        response = self.get_nps_metrics({})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")

    def test_cannot_get_nps_metrics_without_permission(self):
        response = self.get_nps_metrics({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_cannot_get_nps_metrics_without_required_params(self):
        response = self.get_nps_metrics({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["widget_uuid"][0].code, "required")
        self.assertEqual(response.data["start_date"][0].code, "required")
        self.assertEqual(response.data["end_date"][0].code, "required")
        self.assertEqual(response.data["type"][0].code, "required")

    @with_project_auth
    def test_get_nps_metrics_human(self):
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="flowruns",
            type="flow_result",
            position=[1, 2],
            config={
                "filter": {
                    "flow": "123",
                    "op_field": "nps",
                },
                "operation": "recurrence",
                "op_field": "result",
            },
        )

        response = self.get_nps_metrics(
            {
                "project_uuid": self.project.uuid,
                "widget_uuid": widget.uuid,
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
                "type": NpsMetricsType.HUMAN,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn("total_responses", response.data)
        self.assertIn("promoters", response.data)
        self.assertIn("passives", response.data)
        self.assertIn("detractors", response.data)
        self.assertIn("score", response.data)

        fields = [
            response.data[field] for field in ("promoters", "passives", "detractors")
        ]

        for field in fields:
            self.assertIn("value", field)
            self.assertIn("full_value", field)

    @with_project_auth
    def test_get_nps_metrics_ai(self):
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="flowruns",
            type="flow_result",
            position=[1, 2],
            config={
                "filter": {
                    "flow": "123",
                    "op_field": "nps",
                },
                "operation": "recurrence",
                "op_field": "result",
                "datalake_config": {
                    "agent_uuid": str(uuid.uuid4()),
                },
            },
        )

        response = self.get_nps_metrics(
            {
                "project_uuid": self.project.uuid,
                "widget_uuid": widget.uuid,
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
                "type": NpsMetricsType.AI,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn("total_responses", response.data)
        self.assertIn("promoters", response.data)
        self.assertIn("passives", response.data)
        self.assertIn("detractors", response.data)
        self.assertIn("score", response.data)

        fields = [
            response.data[field] for field in ("promoters", "passives", "detractors")
        ]

        for field in fields:
            self.assertIn("value", field)
            self.assertIn("full_value", field)
