import json
import logging

import requests
from django.conf import settings

from insights.internals.base import InternalJWTAuthentication
from insights.sources.clients import GenericSQLQueryGenerator


logger = logging.getLogger(__name__)


class RoomSQLQueryGenerator(GenericSQLQueryGenerator):
    default_query_type = "count"


class RoomRESTClient(InternalJWTAuthentication):
    def __init__(self, project) -> None:
        self.project = project
        self.url = f"{settings.CHATS_URL}/v1/internal/rooms/"

    def list(self, query_filters: dict):
        query_filters["project"] = str(self.project.uuid)

        response = requests.get(
            url=self.url, headers=self.headers, params=query_filters
        )
        try:
            return response.json()
        except json.JSONDecodeError as exc:
            logger.warning(
                "Chats rooms API returned empty/invalid JSON: status=%s url=%s body=%s",
                response.status_code,
                response.url,
                response.text[:500],
            )
            raise exc
