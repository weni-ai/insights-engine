from unittest.mock import patch

from django.test import TestCase

from insights.dashboards.models import CONVERSATIONS_DASHBOARD_NAME, Dashboard
from insights.metrics.conversations.usecases.should_show_dashboard_mock import (
    ShouldShowConversationsDashboardMockUseCase,
)
from insights.projects.models import Project
from insights.widgets.models import Widget


CACHE_MODULE = (
    "insights.metrics.conversations.usecases.should_show_dashboard_mock.cache"
)


class TestShouldShowMockCacheInvalidation(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.dashboard = Dashboard.objects.create(
            project=self.project,
            name=CONVERSATIONS_DASHBOARD_NAME,
            description="Conversations dashboard",
            config={},
        )
        self.cache_key = (
            f"{ShouldShowConversationsDashboardMockUseCase.CACHE_KEY_PREFIX}"
            f":{self.project.uuid}"
        )

    @patch(CACHE_MODULE)
    def test_cache_invalidated_on_widget_create(self, mock_cache):
        Widget.objects.create(
            dashboard=self.dashboard,
            name="custom",
            type="conversations.custom",
            source="conversations.custom",
            config={},
            position={},
        )

        mock_cache.delete.assert_called_with(self.cache_key)

    @patch(CACHE_MODULE)
    def test_cache_invalidated_on_widget_delete(self, mock_cache):
        widget = Widget.objects.create(
            dashboard=self.dashboard,
            name="custom",
            type="conversations.custom",
            source="conversations.custom",
            config={},
            position={},
        )
        mock_cache.reset_mock()

        widget.delete()

        mock_cache.delete.assert_called_with(self.cache_key)

    @patch(CACHE_MODULE)
    def test_cache_not_affected_for_different_dashboard(self, mock_cache):
        other_dashboard = Dashboard.objects.create(
            project=self.project,
            name="other_dashboard",
            description="Other dashboard",
            config={},
        )

        Widget.objects.create(
            dashboard=other_dashboard,
            name="custom",
            type="conversations.custom",
            source="conversations.custom",
            config={},
            position={},
        )

        mock_cache.delete.assert_not_called()
