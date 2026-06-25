from insights.dashboards.models import CONVERSATIONS_DASHBOARD_NAME, Dashboard


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
        return dashboard
