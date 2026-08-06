import json
import logging

import requests
from django.conf import settings

from insights.internals.base import InternalJWTAuthentication
from insights.sources.clients import GenericSQLQueryGenerator


logger = logging.getLogger(__name__)


class AgentSQLQueryGenerator(GenericSQLQueryGenerator):
    default_query_type = "list"


def _parse_chats_json(response: requests.Response) -> dict:
    try:
        return response.json()
    except json.JSONDecodeError as exc:
        logger.warning(
            "Chats API returned empty/invalid JSON: status=%s url=%s body=%s",
            response.status_code,
            response.url,
            response.text[:500],
        )
        raise exc


class AgentsRESTClient(InternalJWTAuthentication):
    def __init__(self, project) -> None:
        self.project = project
        self.base_url = (
            f"{settings.CHATS_URL}/v1/internal/dashboard/{self.project.uuid}"
        )
        self.url = f"{self.base_url}/agent/"

    def list(self, query_filters: dict):
        if query_filters.get("created_on__gte", None):
            query_filters["start_date"] = query_filters.pop("created_on__gte")
        if query_filters.get("created_on__lte", None):
            query_filters["end_date"] = query_filters.pop("created_on__lte")

        response = requests.get(
            url=self.url, headers=self.headers, params=query_filters
        )
        return _parse_chats_json(response)

    def agents_totals(self, query_filters: dict):
        url = f"{self.base_url}/agents_totals/"
        response = requests.get(
            url=url, headers=self.headers, params=query_filters
        )
        return _parse_chats_json(response)
