from insights.dashboards.models import Dashboard
from insights.projects.models import Project


CONVERSATION_DASHBOARD_NAME = "weni_conversations_dashboard"


class ConversationDashboardCreation:
    """
    This class is used to create a conversation dashboard for a project.
    """

    @classmethod
    def create_for_project(cls, project: Project):
        if existing_dashboard := Dashboard.objects.filter(
            project=project,
            name=CONVERSATION_DASHBOARD_NAME,
        ).first():
            return existing_dashboard

        dashboard = Dashboard.objects.create(
            project=project,
            name=CONVERSATION_DASHBOARD_NAME,
            description="Conversations dashboard",
            grid=[],
            is_deletable=False,
            is_editable=False,
        )

        return dashboard
