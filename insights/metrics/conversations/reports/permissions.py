from django.conf import settings
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import ValidationError
from weni.feature_flags.shortcuts import is_feature_active

from insights.projects.models import Project, ProjectAuth


class CanCheckReportGenerationStatusPermission(BasePermission):
    def has_permission(self, request, view):
        project_uuid = request.query_params.get("project_uuid")

        if not project_uuid:
            raise ValidationError(
                {"project_uuid": ["This field is required"]}, code="required"
            )

        project = Project.objects.filter(uuid=project_uuid).first()

        if not project:
            return False

        if not ProjectAuth.objects.filter(
            project__uuid=project_uuid, user=request.user, role=1
        ).exists():
            return False

        return is_feature_active(
            settings.CONVERSATIONS_REPORT_FEATURE_FLAG_KEY,
            request.user.email,
            project.uuid,
        )


class CanGenerateConversationsReportPermission(BasePermission):
    def has_permission(self, request, view):
        project_uuid = request.data.get("project_uuid")

        if not project_uuid:
            raise ValidationError(
                {"project_uuid": ["This field is required"]}, code="required"
            )

        project = Project.objects.filter(uuid=project_uuid).first()

        if not project:
            return False

        if not ProjectAuth.objects.filter(
            project__uuid=project_uuid, user=request.user, role=1
        ).exists():
            return False

        return is_feature_active(
            settings.CONVERSATIONS_REPORT_FEATURE_FLAG_KEY,
            request.user.email,
            project.uuid,
        )
