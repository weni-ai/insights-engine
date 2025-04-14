import requests
from django.conf import settings

from insights.internals.base import InternalAuthentication
from insights.sources.clients import GenericSQLQueryGenerator


class RoomSQLQueryGenerator(GenericSQLQueryGenerator):
    default_query_type = "count"


class RoomRESTClient(InternalAuthentication):
    def __init__(self, project) -> None:
        self.project = project
        self.url = f"{settings.CHATS_URL}/v1/internal/rooms/"

    def list(self, query_filters: dict):
        query_filters["project"] = str(self.project.uuid)
        
        # Converter setores separados por vírgula para lista
        if 'sector' in query_filters and ',' in query_filters['sector']:
            sectors = query_filters['sector'].split(',')
            query_filters.pop('sector')
            query_filters['sector'] = sectors
        
        print(query_filters)
        response = requests.get(
            url=self.url, headers=self.headers, params=query_filters
        )
        return response.json()
