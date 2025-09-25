import logging


from rest_framework import status
from sentry_sdk import capture_exception

from insights.dashboards.tasks import create_conversation_dashboard
from insights.projects.services.indexer_activation import (
    ProjectIndexerActivationService,
)
from insights.sources.integrations.clients import BaseNexusClient
from insights.sources.cache import CacheClient
from insights.projects.models import Project


logger = logging.getLogger(__name__)


class UpdateNexusMultiAgentsStatusService:
    def __init__(
        self,
        nexus_client: BaseNexusClient,
        cache_client: CacheClient,
        indexer_activation_service: ProjectIndexerActivationService,
    ):
        self.nexus_client = nexus_client
        self.cache_client = cache_client
        self.indexer_activation_service = indexer_activation_service

    def update(self, project: Project) -> bool:
        cache_key = f"nexus_multi_agents_status:{project.uuid}"
        cache_ttl = 10

        if cached_response := self.cache_client.get(cache_key):
            try:
                if not isinstance(cached_response, bool):
                    cached_response = bool(cached_response)

                is_active = cached_response
            except Exception as e:
                logger.error(f"Error parsing cached response: {e}")

        else:
            response = self.nexus_client.get_project_multi_agents_status(project.uuid)

            if not status.is_success(response.status_code):
                logger.error(
                    f"Error fetching multi agents status for project {project.uuid}: {response.text}"
                )
                capture_exception(response.text)

                return False

            is_active = response.json().get("multi_agents", False)

        self.cache_client.set(cache_key, str(is_active), cache_ttl)

        if is_active and not project.is_nexus_multi_agents_active:
            project.is_nexus_multi_agents_active = True
            project.save(update_fields=["is_nexus_multi_agents_active"])

            if not self.indexer_activation_service.is_project_active_on_indexer(
                project
            ) and not self.indexer_activation_service.is_project_queued(project):
                self.indexer_activation_service.add_project_to_queue(project)

            # The dashboard is created but should NOT be shown in the dashboard list
            # before the indexer is activated
            # because of widgets that needs data from elasticsearch (flowruns)
            # such as the human support widgets for CSAT and NPS
            create_conversation_dashboard.delay(project.uuid)

        return is_active
