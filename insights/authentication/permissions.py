from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.views import APIView
from weni.feature_flags.shortcuts import is_feature_active

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


class FeatureFlagPermission(permissions.BasePermission):
    """
    Permission to check if a feature flag is active for the project in the request.

    Usage: Set feature_flag_key attribute on the view/viewset class.

    Works with:
    - Views that receive project_uuid in query params or body
    - ViewSet detail actions that use dashboard pk in URL
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        feature_key = getattr(view, "feature_flag_key", None)
        if not feature_key:
            return False

        project = self._get_project_from_request(request, view)
        if not project:
            return False

        return is_feature_active(
            feature_key, user=request.user.email, project=project.uuid
        )

    def _get_project_from_request(self, request: Request, view: APIView):
        """Get project from query params, body, or dashboard pk"""
        project_uuid = request.query_params.get("project_uuid") or request.data.get(
            "project_uuid"
        )

        if project_uuid:
            return get_object_or_404(Project, uuid=project_uuid)

        dashboard_pk = view.kwargs.get("pk")
        if dashboard_pk:
            dashboard = get_object_or_404(Dashboard, uuid=dashboard_pk)
            return dashboard.project

        return None


class HasInternalAuthenticationPermission(permissions.BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        jwt_payload = getattr(request, "jwt_payload", None)
        project_uuid = getattr(request, "project_uuid", None)

        return jwt_payload is not None and project_uuid is not None
