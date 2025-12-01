from uuid import UUID
from rest_framework import permissions

from insights.projects.models import ProjectAuth
from insights.widgets.models import Widget


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


class CanViewWidgetQueryParamPermission(permissions.BasePermission):
    """
    Permission that verifies if the user has permission to view a widget.
    """

    def has_permission(self, request, view) -> bool:
        widget_uuid = request.query_params.get("widget_uuid")

        if not widget_uuid:
            return False

        try:
            UUID(widget_uuid)
        except ValueError:
            return False

        widget_exists = Widget.objects.filter(
            uuid=widget_uuid,
            dashboard__project__in=ProjectAuth.objects.filter(
                user=request.user, role=1
            ).values_list("project", flat=True),
        ).exists()

        return widget_exists
