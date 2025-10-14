import logging
from uuid import UUID

from django.conf import settings

from insights.celery import app
from insights.projects.choices import ProjectIndexerActivationStatus
from insights.projects.models import Project, ProjectIndexerActivation
from insights.projects.services.indexer_activation import (
    ProjectIndexerActivationService,
)
from insights.projects.services.update_nexus_multi_agents_status import (
    UpdateNexusMultiAgentsStatusService,
)
from insights.sources.cache import CacheClient
from insights.sources.integrations.clients import NexusClient


logger = logging.getLogger(__name__)

LIMIT = settings.INDEXER_AUTOMATIC_ACTIVATION_LIMIT


@app.task
def activate_indexer():
    """
    Scheduled task to activate the indexer for queued projects.
    """
    logger.info("[ activate_indexer task ] Starting task")

    if not settings.INDEXER_AUTOMATIC_ACTIVATION:
        logger.info(
            "[ activate_indexer task ] Indexer automatic activation is disabled"
        )
        return

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
        try:
            service.activate_project_on_indexer(activation)
        except Exception as e:
            logger.error(
                "[ activate_indexer task ] Error activating project %s: %s",
                activation.project.uuid,
                e,
            )
            activation.status = ProjectIndexerActivationStatus.FAILED
            activation.save(update_fields=["status"])

    logger.info("[ activate_indexer task ] Finished task")


@app.task
def check_nexus_multi_agents_status(project_uuid: UUID):
    """
    Scheduled task to check the status of the multi agents for all projects.
    """
    logger.info("[ check_nexus_multi_agents_status task ] Starting task")

    project = Project.objects.get(uuid=project_uuid)

    if project.is_nexus_multi_agents_active:
        return

    service = UpdateNexusMultiAgentsStatusService(
        nexus_client=NexusClient(),
        cache_client=CacheClient(),
        indexer_activation_service=ProjectIndexerActivationService(),
    )

    service.update(project)
