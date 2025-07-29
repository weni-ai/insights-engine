from rest_framework import permissions

from insights.projects.models import ProjectAuth


class CanCreateWidgetPermission(permissions.BasePermission):
    """
    Permission that verifies if the user has permission to create a widget.
    """

    def has_permission(self, request, view) -> bool:
        if view.action != "create":
            return None

        dashboard_uuid = request.data.get("dashboard")

        return (
            dashboard_uuid
            and ProjectAuth.objects.filter(
                project__dashboards__uuid=dashboard_uuid,
                user=request.user,
                role=1,
            ).exists()
        )
