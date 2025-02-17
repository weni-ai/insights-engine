from rest_framework.permissions import BasePermission

from insights.sources.wabas.clients import WeniIntegrationsClient


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

        integrations_client = WeniIntegrationsClient(project_uuid=project_uuid)
        wabas_data = integrations_client.get_wabas_for_project()
        wabas_ids = {waba.get("waba_id") for waba in wabas_data}

        return waba_id in wabas_ids
