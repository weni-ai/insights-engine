import requests
import math
from django.conf import settings

from insights.authentication.authentication import FlowsInternalAuthentication
from insights.dashboards.usecases.get_flows_token import UpdateContactName
from insights.utils import get_token_flows_authentication


class FlowsContactsRestClient(FlowsInternalAuthentication):
    def get_flows_contacts(
        self,
        pk=None,
        page_number=1,
        page_size=10,
        project_uuid=None,
        flow_uuid=None,
        op_field=None,
        label=None,
        user=None,
    ):
        page_number = int(page_number) if page_number else 1
        page_size = int(page_size) if page_size else 10
        page_from = (page_number - 1) * page_size

        url = f"{settings.FLOWS_ES_DATABASE}/_search"

        params = {
            "_source": "project_uuid,contact_uuid,created_on,contact_name,contact_urn",
            "from": page_from,
            "size": page_size,
        }

        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"project_uuid": project_uuid}},
                        {"term": {"flow_uuid": flow_uuid}},
                        {
                            "nested": {
                                "path": "values",
                                "query": {
                                    "bool": {
                                        "must": [
                                            {"term": {"values.name": op_field}},
                                            {"term": {"values.value": label}},
                                        ]
                                    }
                                },
                            }
                        },
                    ]
                }
            }
        }

        response = requests.get(url, params=params, json=query).json()

        total_items = response["hits"]["total"]["value"]
        total_pages = math.ceil(total_items / page_size)

        data = []
        flows_token = get_token_flows_authentication(project_uuid, user)

        for hit in response["hits"]["hits"]:
            project_uuid_value = hit["_source"].get("project_uuid", "")
            contact_uuid_value = hit["_source"].get("contact_uuid", "")
            link = f"{settings.WENI_DASHBOARD}projects/{project_uuid_value}/studio/contact/read/{contact_uuid_value}"

            name = UpdateContactName(flows_token).get_contact_name(contact_uuid_value)

            formatted_hit = {
                "contact": {"name": name or hit["_source"].get("contact_name", "")},
                "urn": hit["_source"].get("contact_urn", ""),
                "start": hit["_source"].get("created_on", ""),
                "link": {"type": "external", "url": link},
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
