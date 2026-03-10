from datetime import datetime
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

from insights.metrics.conversations.enums import CsatMetricsType
from insights.metrics.conversations.exceptions import (
    ConversationsMetricsError,
    GetProjectAiCsatMetricsError,
)
from insights.metrics.conversations.usecases.get_project_ai_csat_metrics import (
    GetProjectAiCsatMetricsUseCase,
)
from insights.metrics.conversations.services import ConversationsMetricsService
from insights.projects.models import Project


class TestGetProjectAiCsatMetricsUseCase(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.service = MagicMock(spec=ConversationsMetricsService)
        self.use_case = GetProjectAiCsatMetricsUseCase(service=self.service)

    @override_settings(CONVERSATIONS_DASHBOARD_NATIVE_CSAT_AGENT_UUID="test-agent-uuid")
    def test_execute_returns_service_result(self):
        expected = {
            "results": [
                {"label": "1", "value": 100, "full_value": 100},
            ],
        }
        self.service.get_csat_metrics.return_value = expected

        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        result = self.use_case.execute(
            project_uuid=self.project.uuid,
            start_date=start_date,
            end_date=end_date,
        )

        self.assertEqual(result, expected)
        self.service.get_csat_metrics.assert_called_once()
        call_kwargs = self.service.get_csat_metrics.call_args[1]
        self.assertEqual(call_kwargs["project_uuid"], self.project.uuid)
        self.assertEqual(call_kwargs["start_date"], start_date)
        self.assertEqual(call_kwargs["end_date"], end_date)
        self.assertEqual(call_kwargs["metric_type"], CsatMetricsType.AI)
        widget = call_kwargs["widget"]
        self.assertEqual(
            widget.config["datalake_config"]["agent_uuid"],
            "test-agent-uuid",
        )

    @override_settings(
        CONVERSATIONS_DASHBOARD_NATIVE_CSAT_AGENT_UUID="native-csat-agent"
    )
    def test_execute_calls_service_with_widget_using_agent_uuid_from_settings(self):
        self.service.get_csat_metrics.return_value = {"results": []}

        self.use_case.execute(
            project_uuid=self.project.uuid,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
        )

        call_kwargs = self.service.get_csat_metrics.call_args[1]
        self.assertEqual(
            call_kwargs["widget"].config["datalake_config"]["agent_uuid"],
            "native-csat-agent",
        )

    @override_settings(CONVERSATIONS_DASHBOARD_NATIVE_CSAT_AGENT_UUID="test-agent")
    @patch(
        "insights.metrics.conversations.usecases.get_project_ai_csat_metrics.capture_exception"
    )
    def test_execute_raises_get_project_ai_csat_metrics_error_on_service_error(
        self, mock_capture_exception
    ):
        mock_capture_exception.return_value = "sentry-event-123"
        self.service.get_csat_metrics.side_effect = ConversationsMetricsError(
            "Datalake unavailable"
        )

        with self.assertRaises(GetProjectAiCsatMetricsError) as ctx:
            self.use_case.execute(
                project_uuid=self.project.uuid,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31),
            )

        self.assertEqual(ctx.exception.event_id, "sentry-event-123")
        self.assertIn("Datalake unavailable", str(ctx.exception))
        self.assertIs(
            ctx.exception.__cause__, self.service.get_csat_metrics.side_effect
        )

    def test_execute_uses_injected_service(self):
        self.service.get_csat_metrics.return_value = {"results": []}

        with override_settings(CONVERSATIONS_DASHBOARD_NATIVE_CSAT_AGENT_UUID="agent"):
            self.use_case.execute(
                project_uuid=self.project.uuid,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31),
            )

        self.service.get_csat_metrics.assert_called_once()
