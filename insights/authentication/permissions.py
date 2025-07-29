from rest_framework import permissions
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.views import APIView

from insights.dashboards.models import Dashboard
from insights.projects.models import Project, ProjectAuth


class ProjectAuthPermission(permissions.BasePermission):
    """
    Permission that verifies if the user has access to the project.
    """

    def has_object_permission(self, request, view, obj) -> bool:
        if isinstance(obj, Project):
            project = obj
        else:
            assert hasattr(obj, "project"), "Object must have a project attribute"
            project = obj.project

        return ProjectAuth.objects.filter(
            project=project, user=request.user, role=1
        ).exists()


class CanCreateWidgetPermission(permissions.BasePermission):
    """
    Permission that verifies if the user has permission to create a widget.
    """

    def has_permission(self, request, view) -> bool:
        dashboard_uuid = request.data.get("dashboard")

        if not dashboard_uuid:
            return False

        return ProjectAuth.objects.filter(
            project__dashboards__uuid=dashboard_uuid,
            user=request.user,
            role=1,
        ).exists()


class ProjectAuthQueryParamPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        project_uuid = request.query_params.get("project_uuid")

        if not project_uuid:
            raise ValidationError(
                {"project_uuid": ["This field is required"]}, code="required"
            )

        return ProjectAuth.objects.filter(
            project__uuid=project_uuid, user=request.user, role=1
        ).exists()


class InternalAuthenticationPermission(permissions.BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return request.user.has_perm("users.can_communicate_internally")


class IsServiceAuthentication(permissions.BasePermission):
    """
    Permission that verifies if the request was authenticated via service token.
    """

    def has_permission(self, request, view):
        return request.auth == "service"
