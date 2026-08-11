import logging

import requests
from django.conf import settings

from insights.internals.base import InternalJWTAuthentication


logger = logging.getLogger(__name__)


class ChatsTimeMetricsClient(InternalJWTAuthentication):
    def __init__(self, project) -> None:
        self.project = project
        self.base_url = settings.CHATS_URL

    def _get_json(self, response: requests.Response) -> dict:
        try:
            response.raise_for_status()
            return response.json()
        except requests.HTTPError:
            logger.warning(
                "Chats time metrics API error: status=%s url=%s body=%s",
                response.status_code,
                response.url,
                response.text[:500],
            )
            raise
        except ValueError as exc:
            logger.warning(
                "Chats time metrics API returned empty/invalid JSON: "
                "status=%s url=%s body=%s",
                response.status_code,
                response.url,
                response.text[:500],
            )
            raise exc

    def retrieve_time_metrics(self, params: dict | None = None) -> dict:
        url = self.base_url + f"/v1/dashboard/{self.project.uuid}/time_metrics/"
        response = requests.get(
            url=url,
            headers=self.headers,
            params=params or {},
            timeout=60,
        )
        return self._get_json(response)

    def retrieve_time_metrics_for_analysis(self, params: dict | None = None) -> dict:
        url = (
            self.base_url
            + f"/v1/dashboard/{self.project.uuid}/time_metrics_for_analysis/"
        )
        response = requests.get(
            url=url,
            headers=self.headers,
            params=params or {},
            timeout=60,
        )
        return self._get_json(response)
