from datetime import datetime
import logging
from rest_framework import status as http_status

from insights.sources.integrations.clients import WeniIntegrationsClient

logger = logging.getLogger(__name__)


def format_message_metrics_data(data: dict):
    dt = str(datetime.fromtimestamp(data.get("start")).date())

    return {
        "date": dt,
        "sent": data.get("sent"),
        "delivered": data.get("delivered"),
        "read": data.get("read"),
        "clicked": sum([btn.get("count", 0) for btn in data.get("clicked", [])]),
    }


def format_messages_metrics_data(data: dict) -> dict:
    data_points: dict = data.get("data_points", [])

    status_count = {
        "sent": {
            "value": 0,
        },
        "delivered": {
            "value": 0,
        },
        "read": {
            "value": 0,
        },
        "clicked": {
            "value": 0,
        },
    }
    formatted_data_points = []

    for data in data_points:
        result = format_message_metrics_data(data)

        formatted_data_points.append(result)

        for status in ("sent", "delivered", "read", "clicked"):
            status_count[status]["value"] += result.get(status)

    for status in ("delivered", "read", "clicked"):
        status_count[status]["percentage"] = (
            round(
                (status_count[status]["value"] / status_count["sent"]["value"]) * 100, 2
            )
            if status_count["sent"]["value"] > 0
            else 0
        )

    return {"status_count": status_count, "data_points": formatted_data_points}


def format_button_metrics_data(buttons: list, data_points: list[dict]) -> dict:
    sent = 0
    buttons_data = {}

    for button in buttons:
        buttons_data[button.get("text")] = {"type": button.get("type"), "clicked": 0}

    for data in data_points:
        sent += data.get("sent")

        if not (clicked_buttons := data.get("clicked", None)):
            continue

        for btn in clicked_buttons:
            key = btn.get("button_content")

            if key not in buttons_data:
                continue

            buttons_data[key]["clicked"] += btn.get("count")

    response = []

    for key, btn_data in buttons_data.items():
        click_rate = 0 if sent == 0 else round((btn_data["clicked"] / sent) * 100, 2)

        btn = {
            "label": key,
            "type": btn_data.get("type"),
            "total": btn_data.get("clicked"),
            "click_rate": click_rate,
        }
        response.append(btn)

    return response


def get_edit_template_url_from_template_data(
    project_uuid: str, template_id: dict
) -> str:
    """
    Get the redirect URL from the template data.

    The frontend application will use this URL to redirect the user to the template editor.
    """
    weni_integrations_client = WeniIntegrationsClient()

    response = weni_integrations_client.get_template_data_by_id(
        project_uuid, template_id
    )

    if not response or not http_status.is_success(response.status_code):
        logger.error(
            "Failed to get template data for project_uuid=%s, template_id=%s: %s - %s",
            project_uuid,
            template_id,
            response.status_code,
            response.text,
        )
        return None

    template_data = response.json()

    if not isinstance(template_data, list):
        logger.error(
            "Invalid template data for project_uuid=%s, template_id=%s: %s",
            project_uuid,
            template_id,
            template_data,
        )
        return None

    app_uuid = template_data[0].get("app_uuid")
    templates_uuid = template_data[0].get("templates_uuid", [])

    if len(templates_uuid) < 1:
        logger.error(
            "No templates_uuid found for project_uuid=%s, template_id=%s",
            project_uuid,
            template_id,
        )
        return None

    template_uuid = templates_uuid[0]

    url = f"integrations:apps/my/wpp-cloud/{app_uuid}/templates/edit/{template_uuid}"

    return {"url": url, "type": "internal"}
