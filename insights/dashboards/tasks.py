import logging

from insights.celery import app
from insights.dashboards.usecases.check_and_create_ctwa_dashboard import (
    CheckAndCreateCTWADashboardUseCase,
)
from insights.dashboards.usecases.conversations_dashboard_creation import (
    CreateConversationsDashboard,
)
from insights.projects.models import Project


logger = logging.getLogger(__name__)


@app.task
def check_and_create_ctwa_dashboard(project_uuid: str):
    """
    Check Flows campaigns and create the CTWA dashboard when the project has any.
    """
    logger.info(
        "[ check_and_create_ctwa_dashboard task ] Starting task for project %s",
        project_uuid,
    )
    CheckAndCreateCTWADashboardUseCase().execute(project_uuid)
    logger.info(
        "[ check_and_create_ctwa_dashboard task ] Finished task for project %s",
        project_uuid,
    )


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

    CreateConversationsDashboard().create_dashboard(project)

    logger.info(
        "[ create_conversation_dashboard task ] Conversation dashboard created for project %s",
        project.uuid,
    )
