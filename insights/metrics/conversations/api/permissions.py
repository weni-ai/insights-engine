from django.core.exceptions import ValidationError
from django.db.models import Q
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

        try:
            widget = Widget.objects.filter(
                Q(uuid=widget_uuid)
                & (
                    Q(
                        dashboard__project__in=ProjectAuth.objects.filter(
                            user=request.user
                        ).values_list("project", flat=True)
                    )
                    | Q(
                        parent__dashboard__project__in=ProjectAuth.objects.filter(
                            user=request.user
                        ).values_list("project", flat=True)
                    )
                ),
            ).first()
        except (ValueError, ValidationError):
            return False

        if not widget:
            return False

        return True
