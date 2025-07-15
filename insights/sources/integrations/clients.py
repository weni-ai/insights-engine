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

    def __init__(self):
        self.base_url = settings.NEXUS_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {settings.NEXUS_API_TOKEN}",
        }
        self.timeout = 60

    def get_topics(self, project_uuid: UUID) -> tuple[dict, int]:
        """
        Get conversation topics for a project.
        """
        url = f"{self.base_url}/{project_uuid}/topics/"

        return requests.get(url=url, headers=self.headers, timeout=self.timeout)

    def get_subtopics(self, project_uuid: UUID, topic_id: UUID) -> tuple[dict, int]:
        """
        Get subtopics for a topic.
        """

        url = f"{self.base_url}/{project_uuid}/topics/{topic_id}/subtopics/"

        return requests.get(url=url, headers=self.headers, timeout=self.timeout)

    def create_topic(self, project_uuid: UUID, name: str, description: str) -> dict:
        """
        Create a topic for a project.
        """

        url = f"{self.base_url}/{project_uuid}/topics/"

        body = {
            "name": name,
            "description": description,
        }

        return requests.post(
            url=url, headers=self.headers, timeout=self.timeout, json=body
        )

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

        return requests.post(
            url=url, headers=self.headers, timeout=self.timeout, json=body
        )

    def delete_topic(self, project_uuid: UUID, topic_id: UUID) -> dict:
        """
        Delete a topic for a project.
        """

        url = f"{self.base_url}/{project_uuid}/topics/{topic_id}/"

        return requests.delete(url=url, headers=self.headers, timeout=self.timeout)

    def delete_subtopic(
        self, project_uuid: UUID, topic_id: UUID, subtopic_id: UUID
    ) -> dict:
        """
        Delete a subtopic for a project.
        """

        url = (
            f"{self.base_url}/{project_uuid}/topics/{topic_id}/subtopics/{subtopic_id}/"
        )

        return requests.delete(url=url, headers=self.headers, timeout=self.timeout)
