import json
from uuid import UUID
import logging

from sentry_sdk import capture_message
from rest_framework import status

from insights.metrics.conversations.enums import ConversationsMetricsResource
from insights.metrics.conversations.exceptions import ConversationsMetricsError
from insights.metrics.conversations.mixins import ConversationsServiceCachingMixin
from insights.sources.cache import CacheClient
from insights.sources.integrations.clients import NexusClient


logger = logging.getLogger(__name__)


class ConversationsMetricsService(ConversationsServiceCachingMixin):
    """
    Service to get conversations metrics
    """

    def __init__(
        self,
        nexus_client: NexusClient = NexusClient(),
        cache_client: CacheClient = CacheClient(),
        nexus_cache_ttl: int = 60,
    ):
        self.nexus_client = nexus_client
        self.cache_client = cache_client
        self.nexus_cache_ttl = nexus_cache_ttl

    def get_topics(self, project_uuid: UUID) -> dict:
        """
        Get conversation topics
        """

        if cached_results := self._get_cache_for_project_resource(
            project_uuid, ConversationsMetricsResource.TOPICS
        ):
            return json.loads(cached_results)

        try:
            response = self.nexus_client.get_topics(project_uuid)

        except Exception as e:
            logger.error("Error fetching topics for project %s: %s", project_uuid, e)
            capture_message("Error fetching topics for project %s: %s", project_uuid, e)

            raise ConversationsMetricsError(
                f"Error fetching topics for project {project_uuid}"
            ) from e

        try:
            response_content = response.json()
        except Exception as e:
            logger.error("Error parsing topics for project %s: %s", project_uuid, e)
            response_content = response.text

        if not status.is_success(response.status_code):
            logger.error(
                "Error fetching topics for project %s: %s", project_uuid, response.text
            )
            capture_message(
                "Error fetching topics for project %s: %s", project_uuid, response.text
            )

            raise ConversationsMetricsError(
                f"Error fetching topics for project {project_uuid}"
            )

        self._save_cache_for_project_resource(
            project_uuid, ConversationsMetricsResource.TOPICS, response_content
        )

        return response_content

    def get_subtopics(self, project_uuid: UUID, topic_uuid: UUID) -> dict:
        """
        Get conversation subtopics
        """

        if cached_results := self._get_cache_for_project_resource(
            project_uuid, ConversationsMetricsResource.SUBTOPICS
        ):
            return json.loads(cached_results)

        try:
            response = self.nexus_client.get_subtopics(project_uuid, topic_uuid)

        except Exception as e:
            logger.error("Error fetching subtopics for project %s: %s", project_uuid, e)
            capture_message(
                "Error fetching subtopics for project %s: %s", project_uuid, e
            )

            raise ConversationsMetricsError(
                f"Error fetching subtopics for project {project_uuid}"
            ) from e

        try:
            response_content = response.json()
        except Exception as e:
            logger.error("Error parsing topics for project %s: %s", project_uuid, e)
            response_content = response.text

        if not status.is_success(response.status_code):
            logger.error(
                "Error fetching topics for project %s: %s", project_uuid, response.text
            )
            capture_message(
                "Error fetching topics for project %s: %s", project_uuid, response.text
            )

            raise ConversationsMetricsError(
                f"Error fetching topics for project {project_uuid}"
            )

        self._save_cache_for_project_resource(
            project_uuid, ConversationsMetricsResource.SUBTOPICS, response_content
        )

        return response_content

    def create_topic(self, project_uuid: UUID, name: str, description: str) -> dict:
        """
        Create a conversation topic
        """
        try:
            response = self.nexus_client.create_topic(project_uuid, name, description)

        except Exception as e:
            logger.error("Error creating topic for project %s: %s", project_uuid, e)
            raise ConversationsMetricsError(
                f"Error creating topic for project {project_uuid}"
            ) from e

        try:
            response_content = response.json()
        except Exception as e:
            logger.error("Error parsing topics for project %s: %s", project_uuid, e)
            response_content = response.text

        if not status.is_success(response.status_code):
            logger.error(
                "Error creating topic for project %s: %s", project_uuid, response.text
            )
            capture_message(
                "Error creating topic for project %s: %s", project_uuid, response.text
            )

            raise ConversationsMetricsError(
                f"Error creating topic for project {project_uuid}"
            )

        self._save_cache_for_project_resource(
            project_uuid, ConversationsMetricsResource.TOPICS, response_content
        )

        return response_content

    def create_subtopic(
        self, project_uuid: UUID, topic_uuid: UUID, name: str, description: str
    ) -> dict:
        """
        Create a conversation subtopic
        """

        try:
            response = self.nexus_client.delete_topic(project_uuid, topic_uuid)

        except Exception as e:
            logger.error("Error deleting topic for project %s: %s", project_uuid, e)
            raise ConversationsMetricsError(
                f"Error creating subtopic for project {project_uuid}"
            ) from e

        try:
            response_content = response.json()
        except Exception as e:
            logger.error("Error parsing topics for project %s: %s", project_uuid, e)
            response_content = response.text

        if not status.is_success(response.status_code):
            logger.error(
                "Error creating subtopic for project %s: %s",
                project_uuid,
                response.text,
            )
            capture_message(
                "Error creating subtopic for project %s: %s",
                project_uuid,
                response.text,
            )

            raise ConversationsMetricsError(
                f"Error creating subtopic for project {project_uuid}"
            )

        self._save_cache_for_project_resource(
            project_uuid, ConversationsMetricsResource.SUBTOPICS, response_content
        )

        return response_content

    def delete_topic(self, project_uuid: UUID, topic_uuid: UUID) -> dict:
        """
        Delete a conversation topic
        """

        try:
            response = self.nexus_client.delete_topic(project_uuid, topic_uuid)

        except Exception as e:
            logger.error("Error deleting topic for project %s: %s", project_uuid, e)
            raise ConversationsMetricsError(
                f"Error deleting topic for project {project_uuid}"
            ) from e

        try:
            response_content = response.json()
        except Exception as e:
            logger.error("Error parsing topics for project %s: %s", project_uuid, e)
            response_content = response.text

        if not status.is_success(response.status_code):
            logger.error(
                "Error deleting topic for project %s: %s", project_uuid, response.text
            )
            capture_message(
                "Error deleting topic for project %s: %s", project_uuid, response.text
            )

            raise ConversationsMetricsError(
                f"Error deleting topic for project {project_uuid}"
            )

        self._save_cache_for_project_resource(
            project_uuid, ConversationsMetricsResource.TOPICS, response_content
        )

        return response_content

    def delete_subtopic(
        self, project_uuid: UUID, topic_uuid: UUID, subtopic_uuid: UUID
    ) -> dict:
        """
        Delete a conversation subtopic
        """

        try:
            response = self.nexus_client.delete_subtopic(
                project_uuid, topic_uuid, subtopic_uuid
            )

        except Exception as e:
            logger.error("Error deleting subtopic for project %s: %s", project_uuid, e)
            raise ConversationsMetricsError(
                f"Error deleting subtopic for project {project_uuid}"
            ) from e

        try:
            response_content = response.json()
        except Exception as e:
            logger.error("Error parsing topics for project %s: %s", project_uuid, e)
            response_content = response.text

        if not status.is_success(response.status_code):
            logger.error(
                "Error deleting subtopic for project %s: %s",
                project_uuid,
                response.text,
            )
            capture_message(
                "Error deleting subtopic for project %s: %s",
                project_uuid,
                response.text,
            )

            raise ConversationsMetricsError(
                f"Error deleting subtopic for project {project_uuid}"
            )

        self._save_cache_for_project_resource(
            project_uuid, ConversationsMetricsResource.SUBTOPICS, response_content
        )

        return response_content
