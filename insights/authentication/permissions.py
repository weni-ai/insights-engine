from rest_framework import permissions
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.views import APIView

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


class ProjectAuthBodyPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        project_uuid = request.data.get("project_uuid")

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


class ProjectQueryParamPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False

        project_uuid = request.query_params.get("project_uuid")

        if not project_uuid:
            raise ValidationError(
                {"project_uuid": ["This field is required"]}, code="required"
            )

        return ProjectAuth.objects.filter(
            project__uuid=project_uuid, user=request.user
        ).exists()