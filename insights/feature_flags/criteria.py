from typing import Any, Dict

from django.http import HttpRequest

from insights.projects.models import Project


def build_attributes(request: HttpRequest) -> Dict[str, Any]:
    attrs: Dict[str, Any] = {"host": request.get_host(), "path": request.path}
    if getattr(request, "user", None) and request.user.is_authenticated:
        attrs["userEmail"] = getattr(request.user, "email", None)
    project_uuid = request.GET.get("project_uuid") or getattr(request, "data", {}).get(
        "project_uuid"
    )
    if project_uuid:
        attrs["projectUuid"] = str(project_uuid)
        try:
            project = Project.objects.only("org_uuid").get(uuid=project_uuid)
            if project.org_uuid:
                attrs["orgUuid"] = str(project.org_uuid)
        except Project.DoesNotExist:
            pass
    return attrs
