from uuid import UUID

from django.conf import settings

from insights.metrics.conversations.usecases._resolve_project_agent_by_slugs import (
    resolve_project_agent_by_slugs,
)
from insights.sources.integrations.clients import BaseNexusClient, NexusClient


class GetProjectConciergeAgentUseCase:
    """
    Resolve the concierge agent UUID for a project based on configured slugs.
    """

    def __init__(self, nexus_client: BaseNexusClient | None = None):
        self.nexus_client = nexus_client or NexusClient()

    def execute(self, project_uuid: UUID) -> str | None:
        return resolve_project_agent_by_slugs(
            project_uuid=project_uuid,
            agent_slugs=settings.CONVERSATIONS_METRICS_CONCIERGE_AGENT_SLUGS,
            agent_role="concierge",
            nexus_client=self.nexus_client,
        )
