import logging
from insights.celery import app
from insights.dashboards.models import CONVERSATIONS_DASHBOARD_NAME, Dashboard
from insights.dashboards.usecases.conversations_dashboard_creation import (
    CreateConversationsDashboard,
)
from insights.projects.models import Project


logger = logging.getLogger(__name__)


@app.task
def create_conversation_dashboard(project_uuid: str):
    """
    Create the conversation dashboard for all projects.
    """
    project = Project.objects.get(uuid=project_uuid)

    logger.info(
        "[ create_conversation_dashboard task ] Creating conversation dashboard for project %s",
        project.uuid,
    )

    if Dashboard.objects.filter(
        project=project, name=CONVERSATIONS_DASHBOARD_NAME
    ).exists():
        logger.info(
            "[ create_conversation_dashboard task ] Conversation dashboard already exists for project %s",
            project.uuid,
        )
        return

    CreateConversationsDashboard().create_dashboard(project)

    logger.info(
        "[ create_conversation_dashboard task ] Conversation dashboard created for project %s",
        project.uuid,
    )
