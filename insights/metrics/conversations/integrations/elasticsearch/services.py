from datetime import datetime
import math

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
        page_number: int,
    ) -> list[dict]:
        page_number = int(page_number) if page_number else 1
        page_size = int(page_size) if page_size else 100
        page_from = (page_number - 1) * page_size

        params = {
            "_source": "project_uuid,contact_uuid,created_on,modified_on,contact_name,contact_urn,values",
            "from": page_from,
            "size": page_size,
        }

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

        # Handle Elasticsearch 8.x where total can be int or dict
        total = response["hits"]["total"]
        total_items = total if isinstance(total, int) else total["value"]
        total_pages = math.ceil(total_items / page_size)

        data = []

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

        result = {
            "pagination": {
                "current_page": page_number,
                "total_pages": total_pages,
                "page_size": page_size,
                "total_items": total_items,
            },
            "contacts": data,
        }

        return result
