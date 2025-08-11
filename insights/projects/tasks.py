import logging

from django.conf import settings

from insights.celery import app
from insights.projects.choices import ProjectIndexerActivationStatus
from insights.projects.models import ProjectIndexerActivation
from insights.projects.services.indexer_activation import (
    ProjectIndexerActivationService,
)


logger = logging.getLogger(__name__)

LIMIT = settings.INDEXER_AUTOMATIC_ACTIVATION_LIMIT


@app.task
def activate_indexer(project_uuid: str):
    """
    Scheduled task to activate the indexer for queued projects.
    """
    logger.info("[ activate_indexer task ] Starting task")

    pending_activations = ProjectIndexerActivation.objects.filter(
        status=ProjectIndexerActivationStatus.PENDING
    )

    if not pending_activations.exists():
        logger.info("[ activate_indexer task ] No pending activations found")
        return

    qty = pending_activations.count()

    logger.info(
        "[ activate_indexer task ] Found %s pending activations",
        qty,
    )

    if qty > LIMIT:
        logger.info(
            "[ activate_indexer task ] Found more than %s pending activations, limiting to %s",
            qty,
            LIMIT,
        )
        pending_activations = pending_activations[:LIMIT]

    service = ProjectIndexerActivationService()

    for activation in pending_activations:
        logger.info(
            "[ activate_indexer task ] Activating project %s",
            activation.project.uuid,
        )
        service.activate_project_on_indexer(activation)

    logger.info("[ activate_indexer task ] Finished task")
