import logging
import time

import requests
from sentry_sdk import capture_exception

from django.conf import settings

from insights.projects.choices import ProjectIndexerActivationStatus
from insights.projects.models import Project, ProjectIndexerActivation


logger = logging.getLogger(__name__)


class ProjectIndexerActivationService:
    """
    This service is used to activate the indexer for a project.
    """

    def __init__(
        self,
        retries: int = settings.INDEXER_AUTOMATIC_ACTIVATION_RETRIES,
        retry_delay: int = 10,
    ):
        self.retries = retries
        self.retry_delay = retry_delay

    def is_project_active_on_indexer(self, project: Project):
        """
        This method is used to check if the project is active on the indexer.
        """
        return project.is_allowed or str(project.uuid) in settings.PROJECT_ALLOW_LIST

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

    def activate_project_on_indexer(self, activation: ProjectIndexerActivation) -> bool:
        """
        This method is used to activate the project on the indexer.
        """
        url = settings.WEBHOOK_URL
        payload = {
            "project_uuid": activation.project.uuid,
        }
        headers = {"Authorization": f"Bearer {settings.STATIC_TOKEN}"}

        for _ in range(self.retries):
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=60)
                response.raise_for_status()
            except requests.exceptions.RequestException as error:
                logger.error(
                    "[ activate_project_on_indexer ] Failed to call webhook: %s",
                    error,
                    exc_info=True,
                )
                capture_exception(error)
                activation.status = ProjectIndexerActivationStatus.FAILED
                activation.save(update_fields=["status"])
                time.sleep(self.retry_delay)
                continue
            else:
                activation.project.is_allowed = True
                activation.project.save(update_fields=["is_allowed"])
                activation.status = ProjectIndexerActivationStatus.SUCCESS
                activation.save(update_fields=["status"])
                logger.info(
                    "[ activate_project_on_indexer ] Project %s activated on indexer",
                    activation.project.uuid,
                )
                return True

        return False
