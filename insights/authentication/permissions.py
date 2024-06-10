from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

from insights.projects.models import ProjectAuth


class ProjectAuthPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, "dashboard"):
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
