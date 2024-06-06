from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

from insights.projects.models import ProjectAuth


class ProjectAuthPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, "dashboard") and obj.dashboard:
            project_id = obj.dashboard.project_id
        else:
            project_id = obj.project_id

        user = request.user
        auth = ProjectAuth.objects.filter(project=project_id, user=user, role=1).first()
        if not auth:
            raise PermissionDenied("User does not have permission for this project")
        return True
