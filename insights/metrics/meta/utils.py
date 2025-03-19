from rest_framework import status

from insights.sources.wabas.clients import WeniIntegrationsClient


def get_edit_template_url_from_template_data(
    project_uuid: str, template_id: dict
) -> str:
    """
    Get the redirect URL from the template data.

    The frontend application will use this URL to redirect the user to the template editor.
    """
    weni_integrations_client = WeniIntegrationsClient(project_uuid=project_uuid)

    response = weni_integrations_client.get_template_data_by_id(
        project_uuid, template_id
    )

    if not response or not status.is_success(response.status_code):
        return None

    template_data = response.json()
    app_uuid = template_data.get("app_uuid")
    template_uuid = template_data.get("template_uuid")

    return f"integrations:apps/my/wpp-cloud/{app_uuid}/templates/edit/{template_uuid}"
