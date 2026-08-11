import logging

import requests
from django.conf import settings

from insights.core.requests import request_with_retry
from insights.internals.base import InternalJWTAuthentication


logger = logging.getLogger(__name__)


class ChatsClient(InternalJWTAuthentication):
    def __init__(self, project):
        self.project = project
        self.url = settings.CHATS_URL

    def _get_json(self, response: requests.Response) -> dict:
        try:
            response.raise_for_status()
            return response.json()
        except requests.HTTPError:
            logger.warning(
                "Chats API error: status=%s url=%s body=%s",
                response.status_code,
                response.url,
                response.text[:500],
            )
            raise
        except ValueError as exc:
            logger.warning(
                "Chats API returned empty/invalid JSON: status=%s url=%s body=%s",
                response.status_code,
                response.url,
                response.text[:500],
            )
            raise exc

    def get_contacts(self, query_params: dict):
        url = f"{self.url}/v1/internal/contacts/"
        response = requests.get(
            url, headers=self.headers, params=query_params, timeout=60
        )
        return self._get_json(response)

    def get_protocols(self, query_params: dict):
        url = f"{self.url}/v1/internal/rooms/protocols/"
        response = requests.get(
            url, headers=self.headers, params=query_params, timeout=60
        )
        return self._get_json(response)

    def csat_score_by_agents(self, params: dict | None = None) -> dict:
        url = f"{self.url}/v1/internal/dashboard/{self.project.uuid}/csat-score-by-agents/"

        response = requests.get(
            url=url,
            headers=self.headers,
            params=params or {},
        )
        return self._get_json(response)

    def csat_ratings(self, params: dict | None = None) -> dict:
        url = f"{self.url}/v1/internal/dashboard/{self.project.uuid}/csat_ratings/"

        response = requests.get(
            url=url,
            headers=self.headers,
            params=params or {},
        )
        return self._get_json(response)

    def get_internal_rooms_v2(self, query_params: dict):
        response = request_with_retry(
            url=f"{self.url}/v2/internal/rooms/",
            headers=self.headers,
            params=query_params,
            method="GET",
            timeout=60,
            max_retries=3,
        )
        return response.json()
