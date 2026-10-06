import threading
from unittest.mock import MagicMock, patch
from uuid import uuid4

from django.test import TestCase, override_settings

from insights.dashboards.models import CONVERSATIONS_DASHBOARD_NAME, Dashboard
from insights.metrics.conversations.integrations.datalake.services import (
    BaseDatalakeConversationsMetricsService,
)
from insights.metrics.conversations.usecases.should_show_dashboard_mock import (
    ShouldShowConversationsDashboardMockUseCase,
)
from insights.projects.models import Project
from insights.widgets.models import Widget


USE_CASE_MODULE = (
    "insights.metrics.conversations.usecases.should_show_dashboard_mock"
)


class TestShouldShowConversationsDashboardMockUseCase(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.datalake_service = MagicMock(
            spec=BaseDatalakeConversationsMetricsService
        )
        self.use_case = ShouldShowConversationsDashboardMockUseCase(
            datalake_service=self.datalake_service
        )

    def _create_dashboard(self, config=None) -> Dashboard:
        return Dashboard.objects.create(
            project=self.project,
            name=CONVERSATIONS_DASHBOARD_NAME,
            description="Conversations dashboard",
            config=config or {},
        )

    def _create_widget(self, dashboard: Dashboard, **kwargs) -> Widget:
        defaults = {
            "name": "Test Widget",
            "type": "conversations.custom",
            "source": "conversations.custom",
            "config": {},
            "position": {},
        }
        defaults.update(kwargs)
        return Widget.objects.create(dashboard=dashboard, **defaults)

    @patch(f"{USE_CASE_MODULE}.cache")
    def test_execute_returns_cached_value(self, mock_cache):
        mock_cache.get.return_value = True

        result = self.use_case.execute(project_uuid=self.project.uuid)

        self.assertTrue(result)
        self.datalake_service.check_if_conversation_classification_data_exists.assert_not_called()
        mock_cache.set.assert_not_called()

    @patch(f"{USE_CASE_MODULE}.cache")
    def test_execute_returns_cached_false(self, mock_cache):
        mock_cache.get.return_value = False

        result = self.use_case.execute(project_uuid=self.project.uuid)

        self.assertFalse(result)
        self.datalake_service.check_if_conversation_classification_data_exists.assert_not_called()

    @override_settings(CONVERSATIONS_DASHBOARD_MOCK_CHECK_NEGATIVE_TTL=60)
    @patch(f"{USE_CASE_MODULE}.cache")
    def test_execute_returns_true_when_dashboard_does_not_exist(self, mock_cache):
        mock_cache.get.return_value = None

        result = self.use_case.execute(project_uuid=self.project.uuid)

        self.assertTrue(result)
        mock_cache.set.assert_called_once_with(
            f"conversations_dashboard_should_show_mock:{self.project.uuid}",
            True,
            timeout=60,
        )
        self.datalake_service.check_if_conversation_classification_data_exists.assert_not_called()

    @override_settings(CONVERSATIONS_DASHBOARD_MOCK_CHECK_POSITIVE_TTL=86400)
    @patch(f"{USE_CASE_MODULE}.cache")
    def test_execute_returns_false_when_events_are_persisted(self, mock_cache):
        self._create_dashboard(config={"conversations_data": {"has_events": True}})
        mock_cache.get.return_value = None

        result = self.use_case.execute(project_uuid=self.project.uuid)

        self.assertFalse(result)
        self.datalake_service.check_if_conversation_classification_data_exists.assert_not_called()
        mock_cache.set.assert_called_once_with(
            f"conversations_dashboard_should_show_mock:{self.project.uuid}",
            False,
            timeout=86400,
        )

    @override_settings(CONVERSATIONS_DASHBOARD_MOCK_CHECK_POSITIVE_TTL=86400)
    @patch(f"{USE_CASE_MODULE}.cache")
    def test_execute_returns_false_when_configured_widget_exists(self, mock_cache):
        dashboard = self._create_dashboard()
        self._create_widget(dashboard)
        mock_cache.get.return_value = None

        result = self.use_case.execute(project_uuid=self.project.uuid)

        self.assertFalse(result)
        mock_cache.set.assert_called_once_with(
            f"conversations_dashboard_should_show_mock:{self.project.uuid}",
            False,
            timeout=86400,
        )

    @patch(f"{USE_CASE_MODULE}.cache")
    def test_execute_ignores_default_search_term_widget(self, mock_cache):
        dashboard = self._create_dashboard()
        self._create_widget(
            dashboard,
            name="conversations.search_term",
            type="conversations.search_term",
            source="conversations.search_term",
        )
        mock_cache.get.return_value = None
        self.datalake_service.check_if_conversation_classification_data_exists.return_value = (
            False
        )

        result = self.use_case.execute(project_uuid=self.project.uuid)

        self.assertTrue(result)

    @patch(f"{USE_CASE_MODULE}.cache")
    def test_execute_returns_false_for_csat_widget_with_agent_uuid(self, mock_cache):
        dashboard = self._create_dashboard()
        self._create_widget(
            dashboard,
            type="conversations.csat",
            source="conversations.csat",
            config={"datalake_config": {"type": "CSAT", "agent_uuid": str(uuid4())}},
        )
        mock_cache.get.return_value = None

        result = self.use_case.execute(project_uuid=self.project.uuid)

        self.assertFalse(result)

    @patch(f"{USE_CASE_MODULE}.cache")
    def test_execute_returns_false_for_flow_result_csat_widget(self, mock_cache):
        dashboard = self._create_dashboard()
        self._create_widget(
            dashboard,
            type="conversations.csat",
            source="conversations.csat",
            config={
                "type": "flow_result",
                "filter": {"flow": str(uuid4())},
                "op_field": "csat",
            },
        )
        mock_cache.get.return_value = None

        result = self.use_case.execute(project_uuid=self.project.uuid)

        self.assertFalse(result)

    @patch(f"{USE_CASE_MODULE}.cache")
    def test_execute_returns_false_when_sales_funnel_has_data(self, mock_cache):
        self._create_dashboard(config={"sales_funnel": {"has_data": True}})
        mock_cache.get.return_value = None

        result = self.use_case.execute(project_uuid=self.project.uuid)

        self.assertFalse(result)

    @patch(f"{USE_CASE_MODULE}.cache")
    def test_execute_returns_false_for_absolute_numbers_child_widget(self, mock_cache):
        dashboard = self._create_dashboard()
        parent = self._create_widget(
            dashboard,
            name="absolute numbers",
            type="conversations.absolute_numbers",
            source="conversations.absolute_numbers",
        )
        Widget.objects.create(
            parent=parent,
            name="child",
            type="conversations.absolute_numbers.child",
            source="conversations.absolute_numbers.child",
            config={
                "operation": "TOTAL",
                "key": "weni_csat",
                "agent_uuid": str(uuid4()),
            },
            position={},
        )
        mock_cache.get.return_value = None

        result = self.use_case.execute(project_uuid=self.project.uuid)

        self.assertFalse(result)

    @override_settings(CONVERSATIONS_DASHBOARD_MOCK_CHECK_POSITIVE_TTL=86400)
    @patch(f"{USE_CASE_MODULE}.cache")
    def test_execute_persists_has_events_when_datalake_has_data(self, mock_cache):
        dashboard = self._create_dashboard()
        mock_cache.get.return_value = None
        self.datalake_service.check_if_conversation_classification_data_exists.return_value = (
            True
        )

        result = self.use_case.execute(project_uuid=self.project.uuid)

        self.assertFalse(result)
        dashboard.refresh_from_db()
        self.assertTrue(dashboard.config["conversations_data"]["has_events"])
        mock_cache.set.assert_called_once_with(
            f"conversations_dashboard_should_show_mock:{self.project.uuid}",
            False,
            timeout=86400,
        )

    @override_settings(CONVERSATIONS_DASHBOARD_MOCK_CHECK_NEGATIVE_TTL=60)
    @patch(f"{USE_CASE_MODULE}.cache")
    def test_execute_returns_true_when_no_events_and_no_widgets(self, mock_cache):
        self._create_dashboard()
        mock_cache.get.return_value = None
        self.datalake_service.check_if_conversation_classification_data_exists.return_value = (
            False
        )

        result = self.use_case.execute(project_uuid=self.project.uuid)

        self.assertTrue(result)
        mock_cache.set.assert_called_once_with(
            f"conversations_dashboard_should_show_mock:{self.project.uuid}",
            True,
            timeout=60,
        )

    @patch(f"{USE_CASE_MODULE}.capture_exception")
    @patch(f"{USE_CASE_MODULE}.cache")
    def test_execute_does_not_cache_when_datalake_fails(
        self, mock_cache, mock_capture_exception
    ):
        self._create_dashboard()
        mock_cache.get.return_value = None
        self.datalake_service.check_if_conversation_classification_data_exists.side_effect = (
            Exception("datalake down")
        )

        result = self.use_case.execute(project_uuid=self.project.uuid)

        self.assertTrue(result)
        mock_cache.set.assert_not_called()
        mock_capture_exception.assert_called_once()

    @patch(f"{USE_CASE_MODULE}.cache")
    def test_execute_returns_early_without_waiting_for_datalake(self, mock_cache):
        dashboard = self._create_dashboard()
        self._create_widget(dashboard)
        mock_cache.get.return_value = None

        release = threading.Event()

        def blocking_check(*args, **kwargs):
            release.wait(timeout=5)
            return True

        self.datalake_service.check_if_conversation_classification_data_exists.side_effect = (
            blocking_check
        )

        try:
            result = self.use_case.execute(project_uuid=self.project.uuid)
        finally:
            release.set()

        self.assertFalse(result)
