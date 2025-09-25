from insights.celery import app
from insights.dashboards.models import CONVERSATIONS_DASHBOARD_NAME, Dashboard
from insights.dashboards.usecases.conversations_dashboard_creation import (
    CreateConversationsDashboard,
)
from insights.projects.models import Project


@app.task
def create_conversation_dashboard(project_uuid: str):
    """
    Create the conversation dashboard for all projects.
    """
    project = Project.objects.get(uuid=project_uuid)

    if Dashboard.objects.filter(
        project=project, name=CONVERSATIONS_DASHBOARD_NAME
    ).exists():
        return

    CreateConversationsDashboard().create_dashboard(project)
