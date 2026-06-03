from insights.dashboards.models import CONVERSATIONS_DASHBOARD_NAME, Dashboard


class CreateConversationsDashboard:
    def create_dashboard(self, project):
        if Dashboard.objects.filter(
            project=project, name=CONVERSATIONS_DASHBOARD_NAME
        ).exists():
            raise Exception("Conversation dashboard already exists for this project")

        dashboard = Dashboard.objects.create(
            project=project,
            name=CONVERSATIONS_DASHBOARD_NAME,
            description="Conversations dashboard",
            is_default=False,
            grid=[0, 0],
            is_deletable=False,
            is_editable=True,
            config={
                "type": "conversational",
                "show_tool_result": True,
                "show_agent_invocation": True,
            },
        )
        return dashboard
