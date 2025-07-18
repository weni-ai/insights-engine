import json
from uuid import UUID
from insights.metrics.conversations.enums import ConversationsMetricsResource


class ConversationsServiceCachingMixin:
    """
    Mixin to cache conversations metrics.
    """

    def _get_cache_key_for_project_resource(
        self, project_uuid: UUID, resource: ConversationsMetricsResource
    ) -> str:
        """
        Get cache key for a project resource.
        """
        return f"conversations:{resource}:{project_uuid}"

    def _clear_cache_for_project_resource(
        self, project_uuid: UUID, resource: ConversationsMetricsResource
    ):
        """
        Clear cache for a project resource.
        """
        self.cache_client.delete(
            self._get_cache_key_for_project_resource(project_uuid, resource)
        )

    def _save_cache_for_project_resource(
        self, project_uuid: UUID, resource: ConversationsMetricsResource, data: dict
    ):
        """
        Save cache for a project resource.
        """
        self.cache_client.set(
            self._get_cache_key_for_project_resource(project_uuid, resource),
            json.dumps(data),
            self.nexus_cache_ttl,
        )

    def _get_cache_for_project_resource(
        self, project_uuid: UUID, resource: ConversationsMetricsResource
    ) -> dict:
        """
        Get cache for a project resource.
        """
        return self.cache_client.get(
            self._get_cache_key_for_project_resource(project_uuid, resource)
        )
