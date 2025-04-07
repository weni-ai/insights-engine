from django.conf import settings
from rest_framework.permissions import BasePermission

from insights.sources.integrations.clients import WeniIntegrationsClient


class ProjectWABAPermission(BasePermission):
    """
    Permission to check if the user has access to the waba_id
    """

    def has_permission(self, request, view):
        """
        Check if the user has access to the waba_id
        """
        project_uuid = request.query_params.get("project_uuid")
        waba_id = request.query_params.get("waba_id")

        if not project_uuid or not waba_id:
            return False

        # Temporary: just for testing purposes
        if project_uuid == settings.TEMP_TEST_TEMPLATES_DASH_PROJECT_UUID:
            return True

        integrations_client = WeniIntegrationsClient()
        wabas_data = integrations_client.get_wabas_for_project(project_uuid)

        wabas_ids = {waba.get("waba_id") for waba in wabas_data}

        return waba_id in wabas_ids
