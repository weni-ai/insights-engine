from rest_framework.permissions import BasePermission
from rest_framework.exceptions import ValidationError

from insights.dashboards.models import Dashboard
from insights.projects.models import ProjectAuth
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

        integrations_client = WeniIntegrationsClient()

        try:
            wabas_data = integrations_client.get_wabas_for_project(project_uuid)
        except ValueError:
            return False

        wabas_ids = {waba.get("waba_id") for waba in wabas_data}

        return waba_id in wabas_ids


class ProjectDashboardWABAPermission(BasePermission):
    """
    Check if the user has access to the waba_id
    by checking the dashboard config
    """

    def has_permission(self, request, view):
        """
        Check if the user has access to the waba_id by checking the dashboard
        config
        """
        project_uuid = request.query_params.get("project_uuid")
        waba_id = request.query_params.get("waba_id")

        if not project_uuid or not waba_id:
            return False

        return Dashboard.objects.filter(
            project__uuid=project_uuid,
            config__is_whatsapp_integration=True,
            config__waba_id=waba_id,
        ).exists()


class DashboardAccessPermission(BasePermission):
    """
    Permission that verifies if the user has access to the dashboard
    through ProjectAuth. Replicates the logic from BaseFavoriteTemplateSerializer.
    
    Checks if the dashboard UUID (from request body or query params) belongs to a project
    where the user has authorization.
    """

    def has_permission(self, request, view):
        """
        Check if the user has access to the dashboard via ProjectAuth
        """
        # Check in request body first (POST), then query params (GET)
        dashboard_uuid = request.data.get("dashboard") or request.query_params.get(
            "dashboard"
        )

        if not dashboard_uuid:
            raise ValidationError(
                {"dashboard": ["This field is required"]}, code="required"
            )

        # Check if dashboard exists and user has access to its project
        return Dashboard.objects.filter(
            uuid=dashboard_uuid,
            project__in=ProjectAuth.objects.filter(
                user=request.user
            ).values_list("project", flat=True),
        ).exists()
