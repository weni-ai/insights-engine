from django.db import transaction

from insights.dashboards.models import CONVERSATIONS_DASHBOARD_NAME, Dashboard
from insights.widgets.models import Widget


CONVERSATIONS_DASHBOARD_WIDGETS = [
    "conversations.search_term",
    "conversations.product_added_to_cart",
]


class CreateConversationsDashboard:
    def create_dashboard(self, project):
        dashboard, created = Dashboard.objects.get_or_create(
            project=project,
            name=CONVERSATIONS_DASHBOARD_NAME,
            defaults={
                "description": "Conversations dashboard",
                "is_default": False,
                "grid": [0, 0],
                "is_deletable": False,
                "is_editable": True,
                "config": {
                    "type": "conversational",
                    "show_tool_result": True,
                    "show_agent_invocation": True,
                },
            },
        )
        self._create_widgets(dashboard)
        return dashboard

    def _create_widgets(self, dashboard):
        for widget_identifier in CONVERSATIONS_DASHBOARD_WIDGETS:
            Widget.objects.create(
                dashboard=dashboard,
                name=widget_identifier,
                type=widget_identifier,
                source=widget_identifier,
                position=[],
                config={},
            )
