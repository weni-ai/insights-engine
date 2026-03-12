from rest_framework.permissions import BasePermission


from insights.widgets.models import Widget
from insights.projects.models import ProjectAuth


class WidgetQueryParamPermission(BasePermission):
    """
    Permission to check if the user has access to the widget.
    """

    def has_permission(self, request, view):
        widget_uuid = request.query_params.get("widget_uuid")

        if not widget_uuid:
            return False

        widget = Widget.objects.filter(
            uuid=widget_uuid,
            dashboard__project__in=ProjectAuth.objects.filter(
                user=request.user
            ).values_list("project", flat=True),
        ).first()

        if not widget:
            return False

        return True
