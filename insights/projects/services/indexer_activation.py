import logging

from django.conf import settings

from insights.projects.choices import ProjectIndexerActivationStatus
from insights.projects.models import Project, ProjectIndexerActivation


logger = logging.getLogger(__name__)


class ProjectIndexerActivationService:
    """
    This service is used to activate the indexer for a project.
    """

    def is_project_active_on_indexer(self, project: Project):
        """
        This method is used to check if the project is active on the indexer.
        """
        return project.is_allowed or project.uuid in settings.PROJECT_ALLOW_LIST

    def add_project_to_queue(self, project: Project):
        """
        This method is used to add a project to the queue.
        If the project is active on the indexer, it will not be added to the queue.
        """
        if self.is_project_active_on_indexer(project):
            logger.info(
                "[ ProjectIndexerActivationService ] Project %s is active on indexer",
                project.uuid,
            )
            return False

        if ProjectIndexerActivation.objects.filter(
            project=project, status=ProjectIndexerActivationStatus.PENDING
        ).exists():
            logger.info(
                "[ ProjectIndexerActivationService ] Project %s is already in queue",
                project.uuid,
            )
            return False

        ProjectIndexerActivation.objects.create(
            project=project, status=ProjectIndexerActivationStatus.PENDING
        )
        logger.info(
            "[ ProjectIndexerActivationService ] Project %s added to queue",
            project.uuid,
        )
        return True
