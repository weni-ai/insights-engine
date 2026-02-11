from datetime import datetime

from insights.metrics.conversations.integrations.elasticsearch.clients import (
    ElasticsearchClient,
)


class ConversationsElasticsearchService:
    def __init__(self, client: ElasticsearchClient):
        self.client = client

    def _format_date(self, date: str) -> str:
        if isinstance(date, datetime):
            try:
                date = date.isoformat()
            except Exception:
                date = date
        return date

    def get_flowsrun_results_by_contacts(
        self,
        project_uuid: str,
        flow_uuid: str,
        start_date: str,
        end_date: str,
        op_field: str,
        page_size: int,
        search_after: list[str] | None = None,
    ) -> list[dict]:
        params = {
            "_source": "project_uuid,contact_uuid,created_on,modified_on,contact_name,contact_urn,values",
            "size": page_size,
        }

        if search_after:
            params["search_after"] = search_after

        start_date = self._format_date(start_date)
        end_date = self._format_date(end_date)

        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"project_uuid": str(project_uuid)}},
                        {"term": {"flow_uuid": flow_uuid}},
                        {
                            "nested": {
                                "path": "values",
                                "query": {"term": {"values.name": op_field}},
                            }
                        },
                        {
                            "range": {
                                "modified_on": {
                                    "gte": start_date,
                                    "lte": end_date,
                                }
                            }
                        },
                    ]
                }
            },
            "sort": [{"modified_on": {"order": "desc"}}],
        }

        response = self.client.get(endpoint="_search", params=params, query=query)

        data = []

        last_sort = []

        for hit in response["hits"]["hits"]:
            op_field_value = None
            values = hit["_source"].get("values", [])

            for value in values:
                if value.get("name") == op_field:
                    op_field_value = value.get("value")
                    break

            formatted_hit = {
                "contact": {"name": hit["_source"].get("contact_name", "")},
                "urn": hit["_source"].get("contact_urn", ""),
                "modified_on": hit["_source"].get("modified_on", ""),
                "op_field_value": op_field_value,
            }
            data.append(formatted_hit)

            last_sort = hit.get("sort", [])

        result = {
            "pagination": {
                "sort": last_sort,
            },
            "contacts": data,
        }

        return result
