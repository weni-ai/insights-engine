from unittest.mock import patch

from django.test import TestCase

from insights.dashboards.models import CONVERSATIONS_DASHBOARD_NAME, Dashboard
from insights.dashboards.usecases.conversations_dashboard_creation import (
    CreateConversationsDashboard,
)
from insights.projects.models import Project
from insights.widgets.models import Widget


class TestCreateConversationsDashboard(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.usecase = CreateConversationsDashboard()

    def test_create_dashboard_persists_dashboard_with_expected_fields(self):
        dashboard = self.usecase.create_dashboard(self.project)

        self.assertEqual(Dashboard.objects.count(), 1)
        self.assertEqual(dashboard.project, self.project)
        self.assertEqual(dashboard.name, CONVERSATIONS_DASHBOARD_NAME)
        self.assertEqual(dashboard.description, "Conversations dashboard")
        self.assertFalse(dashboard.is_default)
        self.assertFalse(dashboard.is_deletable)
        self.assertTrue(dashboard.is_editable)
        self.assertEqual(dashboard.grid, [0, 0])
        self.assertEqual(
            dashboard.config,
            {
                "type": "conversational",
                "show_tool_result": True,
                "show_agent_invocation": True,
            },
        )

    def test_create_dashboard_creates_search_term_and_product_added_to_cart_widgets(
        self,
    ):
        dashboard = self.usecase.create_dashboard(self.project)

        widgets = Widget.objects.filter(dashboard=dashboard)
        self.assertEqual(widgets.count(), 2)

        search_term_widget = widgets.get(name="conversations.search_term")
        self.assertEqual(search_term_widget.type, "conversations.search_term")
        self.assertEqual(search_term_widget.source, "conversations.search_term")
        self.assertEqual(search_term_widget.position, [])
        self.assertEqual(search_term_widget.config, {})

        product_added_widget = widgets.get(name="conversations.product_added_to_cart")
        self.assertEqual(
            product_added_widget.type, "conversations.product_added_to_cart"
        )
        self.assertEqual(
            product_added_widget.source, "conversations.product_added_to_cart"
        )
        self.assertEqual(product_added_widget.position, [])
        self.assertEqual(product_added_widget.config, {})

    def test_create_dashboard_raises_when_dashboard_already_exists(self):
        Dashboard.objects.create(
            project=self.project,
            name=CONVERSATIONS_DASHBOARD_NAME,
            description="Conversations dashboard",
            is_default=False,
            grid=[0, 0],
            is_deletable=False,
            is_editable=True,
            config={},
        )

        with self.assertRaises(Exception) as ctx:
            self.usecase.create_dashboard(self.project)

        self.assertEqual(
            str(ctx.exception),
            "Conversation dashboard already exists for this project",
        )
        self.assertEqual(Dashboard.objects.count(), 1)
        self.assertEqual(Widget.objects.count(), 0)

    def test_create_dashboard_rolls_back_when_widget_creation_fails(self):
        with patch(
            "insights.dashboards.usecases.conversations_dashboard_creation.Widget.objects.create",
            side_effect=Exception("boom"),
        ):
            with self.assertRaises(Exception):
                self.usecase.create_dashboard(self.project)

        self.assertEqual(Dashboard.objects.count(), 0)
        self.assertEqual(Widget.objects.count(), 0)
