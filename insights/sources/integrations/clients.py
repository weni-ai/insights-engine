import logging
from uuid import UUID
import requests
import json

from django.conf import settings
from rest_framework import status
from sentry_sdk import capture_message
from insights.internals.base import InternalAuthentication
from insights.sources.cache import CacheClient
from insights.sources.integrations.enums import NexusResource


logger = logging.getLogger(__name__)


class WeniIntegrationsClient(InternalAuthentication):
    def __init__(self):
        self.base_url = f"{settings.INTEGRATIONS_URL}"
        self.cache = CacheClient()

    def get_wabas_for_project(self, project_uuid: str):
        url = f"{self.base_url}/api/v1/apptypes/wpp-cloud/list_wpp-cloud/{project_uuid}"
        cache_key = f"wabas:{project_uuid}"
        cache_ttl = 60  # 1m

        if cached_response := self.cache.get(cache_key):
            return json.loads(cached_response)

        response = requests.get(url=url, headers=self.headers, timeout=60)

        if not status.is_success(response.status_code):
            logger.error(
                "Error fetching wabas for project %s: %s - %s",
                project_uuid,
                response.status_code,
                response.text,
            )
            capture_message(response.text)

            raise ValueError(response.text)

        wabas = response.json().get("data", [])

        self.cache.set(cache_key, json.dumps(wabas), cache_ttl)

        return wabas

    def get_template_data_by_id(self, project_uuid: str, template_id: str):
        url = f"{self.base_url}/api/v1/project/templates/details/"

        response = requests.get(
            url=url,
            headers=self.headers,
            timeout=60,
            params={"project_uuid": project_uuid, "template_id": template_id},
        )

        return response


class NexusClient:
    """
    Client for Nexus API.
    """

    def __init__(self, cache_client: CacheClient = CacheClient):
        self.base_url = settings.NEXUS_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {settings.NEXUS_API_TOKEN}",
        }
        self.timeout = 60
        self.cache = cache_client()
        self.cache_ttl = 60

    def _get_cache_key_for_project_resource(
        self, project_uuid: UUID, resource: NexusResource
    ) -> str:
        """
        Get cache key for a project resource.
        """
        return f"nexus:{resource}:{project_uuid}"

    def _clear_cache_for_project_resource(
        self, project_uuid: UUID, resource: NexusResource
    ):
        """
        Clear cache for a project resource.
        """
        self.cache.delete(
            self._get_cache_key_for_project_resource(project_uuid, resource)
        )

    def _save_cache_for_project_resource(
        self, project_uuid: UUID, resource: NexusResource, data: dict
    ):
        """
        Save cache for a project resource.
        """
        self.cache.set(
            self._get_cache_key_for_project_resource(project_uuid, resource),
            json.dumps(data),
            self.cache_ttl,
        )

    def _get_cache_for_project_resource(
        self, project_uuid: UUID, resource: NexusResource
    ) -> dict:
        """
        Get cache for a project resource.
        """
        return self.cache.get(
            self._get_cache_key_for_project_resource(project_uuid, resource)
        )

    def get_topics(self, project_uuid: UUID) -> tuple[dict, int]:
        """
        Get conversation topics for a project.
        """

        if cached_response := self._get_cache_for_project_resource(
            project_uuid, NexusResource.TOPICS
        ):
            return json.loads(cached_response), status.HTTP_200_OK

        url = f"{self.base_url}/{project_uuid}/topics/"

        try:
            response = requests.get(url=url, headers=self.headers, timeout=self.timeout)
        except Exception as e:
            logger.error("Error fetching topics for project %s: %s", project_uuid, e)
            capture_message("Error fetching topics for project %s: %s", project_uuid, e)
            raise e

        if not status.is_success(response.status_code):
            logger.error(
                "Error fetching topics for project %s: %s", project_uuid, response.text
            )
            capture_message(
                "Error fetching topics for project %s: %s", project_uuid, response.text
            )

            return (
                {"error": f"Error fetching topics for project {project_uuid}"},
                response.status_code,
            )

        response_content = response.json()

        self._save_cache_for_project_resource(
            project_uuid, NexusResource.TOPICS, response_content
        )

        return response_content, status.HTTP_200_OK

    def get_subtopics(self, project_uuid: UUID, topic_id: UUID) -> tuple[dict, int]:
        """
        Get subtopics for a topic.
        """

        if cached_response := self._get_cache_for_project_resource(
            project_uuid, NexusResource.SUBTOPICS
        ):
            return json.loads(cached_response), status.HTTP_200_OK

        url = f"{self.base_url}/{project_uuid}/topics/{topic_id}/subtopics/"

        try:
            response = requests.get(url=url, headers=self.headers, timeout=self.timeout)
        except Exception as e:
            logger.error("Error fetching subtopics for project %s: %s", project_uuid, e)
            capture_message(
                "Error fetching subtopics for project %s: %s", project_uuid, e
            )
            raise e

        if not status.is_success(response.status_code):
            logger.error(
                "Error fetching subtopics for project %s: %s",
                project_uuid,
                response.text,
            )
            capture_message(
                "Error fetching subtopics for project %s: %s",
                project_uuid,
                response.text,
            )

        response_content = response.json()

        self._save_cache_for_project_resource(
            project_uuid, NexusResource.SUBTOPICS, response_content
        )

        return response_content, status.HTTP_200_OK

    def create_topic(self, project_uuid: UUID, name: str, description: str) -> dict:
        """
        Create a topic for a project.
        """

        url = f"{self.base_url}/{project_uuid}/topics/"

        body = {
            "name": name,
            "description": description,
        }

        try:
            response = requests.post(
                url=url, headers=self.headers, timeout=self.timeout, json=body
            )
        except Exception as e:
            logger.error("Error creating topic for project %s: %s", project_uuid, e)
            capture_message("Error creating topic for project %s: %s", project_uuid, e)
            raise e

        if not status.is_success(response.status_code):
            logger.error(
                "Error creating topic for project %s: %s", project_uuid, response.text
            )
            capture_message(
                "Error creating topic for project %s: %s", project_uuid, response.text
            )

            return (
                {"error": f"Error creating topic for project {project_uuid}"},
                response.status_code,
            )

        response_content = response.json()

        self._clear_cache_for_project_resource(project_uuid, NexusResource.TOPICS)

        return response_content, status.HTTP_200_OK

    def create_subtopic(
        self, project_uuid: UUID, topic_id: UUID, name: str, description: str
    ) -> dict:
        """
        Create a subtopic for a project.
        """

        url = f"{self.base_url}/{project_uuid}/topics/{topic_id}/subtopics/"

        body = {
            "name": name,
            "description": description,
        }

        try:
            response = requests.post(
                url=url, headers=self.headers, timeout=self.timeout, json=body
            )
        except Exception as e:
            logger.error("Error creating subtopic for project %s: %s", project_uuid, e)
            capture_message(
                "Error creating subtopic for project %s: %s", project_uuid, e
            )

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

            return (
                {"error": f"Error creating subtopic for project {project_uuid}"},
                response.status_code,
            )

        response_content = response.json()

        self._clear_cache_for_project_resource(project_uuid, NexusResource.SUBTOPICS)

        return response_content, status.HTTP_200_OK
