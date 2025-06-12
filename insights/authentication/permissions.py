from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.request import Request
from rest_framework.views import APIView

from insights.projects.models import Project, ProjectAuth


class ProjectAuthPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if type(obj) is Project:
            project = obj
        else:
            project = obj.project

        user = request.user
        auth = ProjectAuth.objects.filter(project=project, user=user, role=1).first()
        if not auth:
            raise PermissionDenied("User does not have permission for this project")
        return True


class WidgetAuthPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        project = obj.dashboard.project
        user = request.user
        auth = ProjectAuth.objects.filter(project=project, user=user, role=1).first()
        if not auth:
            raise PermissionDenied("User does not have permission for this project")
        return True


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
