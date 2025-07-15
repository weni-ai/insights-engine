from abc import ABC, abstractmethod
import logging
from uuid import UUID
import requests
from requests.models import Response
import json


from django.conf import settings
from rest_framework import status
from sentry_sdk import capture_message
from insights.internals.base import InternalAuthentication
from insights.sources.cache import CacheClient


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


class BaseNexusClient(ABC):
    """
    Base client for Nexus API.
    """

    @abstractmethod
    def get_topics(self, project_uuid: UUID) -> Response:
        """
        Get conversation topics for a project.
        """

    @abstractmethod
    def get_subtopics(self, project_uuid: UUID, topic_id: UUID) -> Response:
        """
        Get conversation subtopics for a topic.
        """

    @abstractmethod
    def create_topic(self, project_uuid: UUID, name: str, description: str) -> Response:
        """
        Create a conversation topic for a project.
        """

    @abstractmethod
    def create_subtopic(
        self, project_uuid: UUID, topic_id: UUID, name: str, description: str
    ) -> Response:
        """
        Create a conversation subtopic for a project.
        """

    @abstractmethod
    def delete_topic(self, project_uuid: UUID, topic_id: UUID) -> Response:
        """
        Delete a conversation topic for a project.
        """

    @abstractmethod
    def delete_subtopic(
        self, project_uuid: UUID, topic_id: UUID, subtopic_id: UUID
    ) -> Response:
        """
        Delete a conversation subtopic for a project.
        """


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

    def get_topics(self, project_uuid: UUID) -> Response:
        """
        Get conversation topics for a project.
        """
        url = f"{self.base_url}/{project_uuid}/topics/"

        return requests.get(url=url, headers=self.headers, timeout=self.timeout)

    def get_subtopics(self, project_uuid: UUID, topic_id: UUID) -> Response:
        """
        Get subtopics for a topic.
        """

        url = f"{self.base_url}/{project_uuid}/topics/{topic_id}/subtopics/"

        return requests.get(url=url, headers=self.headers, timeout=self.timeout)

    def create_topic(self, project_uuid: UUID, name: str, description: str) -> Response:
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
    ) -> Response:
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

    def delete_topic(self, project_uuid: UUID, topic_id: UUID) -> Response:
        """
        Delete a topic for a project.
        """

        url = f"{self.base_url}/{project_uuid}/topics/{topic_id}/"

        return requests.delete(url=url, headers=self.headers, timeout=self.timeout)

    def delete_subtopic(
        self, project_uuid: UUID, topic_id: UUID, subtopic_id: UUID
    ) -> Response:
        """
        Delete a subtopic for a project.
        """

        url = (
            f"{self.base_url}/{project_uuid}/topics/{topic_id}/subtopics/{subtopic_id}/"
        )

        return requests.delete(url=url, headers=self.headers, timeout=self.timeout)
