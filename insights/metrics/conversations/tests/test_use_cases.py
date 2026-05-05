from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4
import uuid

from django.test import TestCase, override_settings
from rest_framework import serializers

from insights.dashboards.models import CONVERSATIONS_DASHBOARD_NAME, Dashboard
from insights.metrics.conversations.enums import CsatMetricsType
from insights.metrics.conversations.integrations.datalake.services import (
    BaseDatalakeConversationsMetricsService,
)
from insights.metrics.conversations.usecases.dashboard_check_project_sales_funnel import (
    CheckProjectSalesFunnelOnDashboardUseCase,
)
from insights.metrics.conversations.usecases.datalake_check_project_sales_funnel import (
    CheckProjectSalesFunnelOnDatalakeUseCase,
)
from insights.metrics.conversations.usecases.get_absolute_numbers_widget import (
    GetAbsoluteNumbersWidgetUseCase,
)
from insights.metrics.conversations.usecases.get_project_ai_csat_metrics import (
    GetProjectAiCsatMetricsUseCase,
)
from insights.metrics.conversations.services import ConversationsMetricsService
from insights.projects.models import Project
from insights.widgets.models import Widget


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
    def test_execute_propagates_service_error(self):
        self.service.get_csat_metrics.side_effect = ValueError(
            "Datalake unavailable"
        )

        with self.assertRaises(ValueError) as ctx:
            self.use_case.execute(
                project_uuid=self.project.uuid,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31),
            )

        self.assertIn("Datalake unavailable", str(ctx.exception))

    def test_execute_uses_injected_service(self):
        self.service.get_csat_metrics.return_value = {"results": []}

        with override_settings(CONVERSATIONS_DASHBOARD_NATIVE_CSAT_AGENT_UUID="agent"):
            self.use_case.execute(
                project_uuid=self.project.uuid,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31),
            )

        self.service.get_csat_metrics.assert_called_once()


class TestGetAbsoluteNumbersWidgetUseCase(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.dashboard = Dashboard.objects.create(
            project=self.project,
            name="Test Dashboard",
            description="Test",
        )
        self.valid_config = {
            "operation": "TOTAL",
            "key": "some_key",
            "agent_uuid": str(uuid.uuid4()),
        }
        self.widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="conversations.absolute_numbers.child",
            config=self.valid_config,
        )
        self.use_case = GetAbsoluteNumbersWidgetUseCase()

    def test_execute_returns_widget_when_valid(self):
        result = self.use_case.execute(widget_uuid=self.widget.uuid)

        self.assertEqual(result.pk, self.widget.pk)

    def test_execute_raises_when_widget_not_found(self):
        with self.assertRaises(serializers.ValidationError) as ctx:
            self.use_case.execute(widget_uuid=uuid4())

        self.assertEqual(ctx.exception.detail["widget_uuid"].code, "widget_not_found")

    def test_execute_raises_when_source_is_not_absolute_numbers_child(self):
        self.widget.source = "conversations.other"
        self.widget.save()

        with self.assertRaises(serializers.ValidationError) as ctx:
            self.use_case.execute(widget_uuid=self.widget.uuid)

        self.assertEqual(
            ctx.exception.detail["widget_uuid"].code,
            "widget_source_not_absolute_numbers_child",
        )

    def test_execute_raises_when_operation_is_not_valid(self):
        self.widget.config = {**self.valid_config, "operation": "INVALID"}
        self.widget.save()

        with self.assertRaises(serializers.ValidationError) as ctx:
            self.use_case.execute(widget_uuid=self.widget.uuid)

        self.assertEqual(
            ctx.exception.detail["widget_uuid"].code,
            "widget_operation_not_valid",
        )

    def test_execute_raises_when_key_is_missing(self):
        self.widget.config = {**self.valid_config, "key": ""}
        self.widget.save()

        with self.assertRaises(serializers.ValidationError) as ctx:
            self.use_case.execute(widget_uuid=self.widget.uuid)

        self.assertEqual(
            ctx.exception.detail["widget_uuid"].code,
            "widget_key_not_valid",
        )

    def test_execute_raises_when_agent_uuid_is_missing(self):
        self.widget.config = {
            "operation": "TOTAL",
            "key": "some_key",
            "datalake_config": {},
        }
        self.widget.save()

        with self.assertRaises(serializers.ValidationError) as ctx:
            self.use_case.execute(widget_uuid=self.widget.uuid)

        self.assertEqual(
            ctx.exception.detail["widget_uuid"].code,
            "widget_agent_uuid_not_valid",
        )


class TestCheckProjectSalesFunnelOnDashboardUseCase(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.use_case = CheckProjectSalesFunnelOnDashboardUseCase()

    def test_execute_returns_false_when_dashboard_does_not_exist(self):
        result = self.use_case.execute(project_uuid=self.project.uuid)

        self.assertFalse(result)

    def test_execute_returns_false_when_config_has_no_sales_funnel(self):
        Dashboard.objects.create(
            project=self.project,
            name=CONVERSATIONS_DASHBOARD_NAME,
            config={},
        )

        result = self.use_case.execute(project_uuid=self.project.uuid)

        self.assertFalse(result)

    def test_execute_returns_false_when_has_data_is_false(self):
        Dashboard.objects.create(
            project=self.project,
            name=CONVERSATIONS_DASHBOARD_NAME,
            config={"sales_funnel": {"has_data": False}},
        )

        result = self.use_case.execute(project_uuid=self.project.uuid)

        self.assertFalse(result)

    def test_execute_returns_true_when_has_data_is_true(self):
        Dashboard.objects.create(
            project=self.project,
            name=CONVERSATIONS_DASHBOARD_NAME,
            config={"sales_funnel": {"has_data": True}},
        )

        result = self.use_case.execute(project_uuid=self.project.uuid)

        self.assertTrue(result)

    def test_execute_returns_false_when_config_is_none(self):
        Dashboard.objects.create(
            project=self.project,
            name=CONVERSATIONS_DASHBOARD_NAME,
            config=None,
        )

        result = self.use_case.execute(project_uuid=self.project.uuid)

        self.assertFalse(result)

    def test_execute_ignores_dashboards_with_different_name(self):
        Dashboard.objects.create(
            project=self.project,
            name="other_dashboard",
            config={"sales_funnel": {"has_data": True}},
        )

        result = self.use_case.execute(project_uuid=self.project.uuid)

        self.assertFalse(result)


class TestCheckProjectSalesFunnelOnDatalakeUseCase(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.datalake_service = MagicMock(
            spec=BaseDatalakeConversationsMetricsService
        )
        self.use_case = CheckProjectSalesFunnelOnDatalakeUseCase(
            datalake_service=self.datalake_service
        )

    def test_execute_returns_false_when_dashboard_does_not_exist(self):
        result = self.use_case.execute(project_uuid=self.project.uuid)

        self.assertFalse(result)
        self.datalake_service.check_if_sales_funnel_data_exists.assert_not_called()

    def test_execute_returns_true_when_dashboard_config_already_has_data(self):
        Dashboard.objects.create(
            project=self.project,
            name=CONVERSATIONS_DASHBOARD_NAME,
            config={"sales_funnel": {"has_data": True}},
        )

        result = self.use_case.execute(project_uuid=self.project.uuid)

        self.assertTrue(result)
        self.datalake_service.check_if_sales_funnel_data_exists.assert_not_called()

    @override_settings(SALES_FUNNEL_CHECK_COOLDOWN_TTL=30)
    @patch("insights.metrics.conversations.usecases.datalake_check_project_sales_funnel.cache")
    def test_execute_returns_cached_value_when_available(self, mock_cache):
        Dashboard.objects.create(
            project=self.project,
            name=CONVERSATIONS_DASHBOARD_NAME,
            config={},
        )
        mock_cache.get.return_value = True

        result = self.use_case.execute(project_uuid=self.project.uuid)

        self.assertTrue(result)
        self.datalake_service.check_if_sales_funnel_data_exists.assert_not_called()

    @override_settings(SALES_FUNNEL_CHECK_COOLDOWN_TTL=30)
    @patch("insights.metrics.conversations.usecases.datalake_check_project_sales_funnel.cache")
    def test_execute_returns_false_when_datalake_has_no_data(self, mock_cache):
        Dashboard.objects.create(
            project=self.project,
            name=CONVERSATIONS_DASHBOARD_NAME,
            config={},
        )
        mock_cache.get.return_value = None
        self.datalake_service.check_if_sales_funnel_data_exists.return_value = False

        result = self.use_case.execute(project_uuid=self.project.uuid)

        self.assertFalse(result)
        mock_cache.set.assert_called_once_with(
            f"sales_funnel_check:{self.project.uuid}",
            False,
            timeout=30,
        )

    @override_settings(SALES_FUNNEL_CHECK_COOLDOWN_TTL=30)
    @patch("insights.metrics.conversations.usecases.datalake_check_project_sales_funnel.cache")
    def test_execute_updates_config_and_creates_widget_when_datalake_has_data(
        self, mock_cache
    ):
        dashboard = Dashboard.objects.create(
            project=self.project,
            name=CONVERSATIONS_DASHBOARD_NAME,
            config={},
        )
        mock_cache.get.return_value = None
        self.datalake_service.check_if_sales_funnel_data_exists.return_value = True

        result = self.use_case.execute(project_uuid=self.project.uuid)

        self.assertTrue(result)
        dashboard.refresh_from_db()
        self.assertTrue(dashboard.config["sales_funnel"]["has_data"])
        self.assertTrue(
            Widget.objects.filter(
                dashboard=dashboard,
                name=CheckProjectSalesFunnelOnDatalakeUseCase.WIDGET_NAME,
                type=CheckProjectSalesFunnelOnDatalakeUseCase.WIDGET_TYPE,
                source=CheckProjectSalesFunnelOnDatalakeUseCase.WIDGET_SOURCE,
            ).exists()
        )

    @override_settings(SALES_FUNNEL_CHECK_COOLDOWN_TTL=30)
    @patch("insights.metrics.conversations.usecases.datalake_check_project_sales_funnel.cache")
    def test_execute_does_not_duplicate_widget_when_already_exists(self, mock_cache):
        dashboard = Dashboard.objects.create(
            project=self.project,
            name=CONVERSATIONS_DASHBOARD_NAME,
            config={},
        )
        Widget.objects.create(
            dashboard=dashboard,
            name=CheckProjectSalesFunnelOnDatalakeUseCase.WIDGET_NAME,
            type=CheckProjectSalesFunnelOnDatalakeUseCase.WIDGET_TYPE,
            source=CheckProjectSalesFunnelOnDatalakeUseCase.WIDGET_SOURCE,
            config={},
            position={},
        )
        mock_cache.get.return_value = None
        self.datalake_service.check_if_sales_funnel_data_exists.return_value = True

        result = self.use_case.execute(project_uuid=self.project.uuid)

        self.assertTrue(result)
        self.assertEqual(
            Widget.objects.filter(
                dashboard=dashboard,
                name=CheckProjectSalesFunnelOnDatalakeUseCase.WIDGET_NAME,
            ).count(),
            1,
        )

    @override_settings(SALES_FUNNEL_CHECK_COOLDOWN_TTL=60)
    @patch("insights.metrics.conversations.usecases.datalake_check_project_sales_funnel.cache")
    def test_execute_caches_datalake_result_with_configured_ttl(self, mock_cache):
        Dashboard.objects.create(
            project=self.project,
            name=CONVERSATIONS_DASHBOARD_NAME,
            config={},
        )
        mock_cache.get.return_value = None
        self.datalake_service.check_if_sales_funnel_data_exists.return_value = True

        self.use_case.execute(project_uuid=self.project.uuid)

        mock_cache.set.assert_called_once_with(
            f"sales_funnel_check:{self.project.uuid}",
            True,
            timeout=60,
        )
