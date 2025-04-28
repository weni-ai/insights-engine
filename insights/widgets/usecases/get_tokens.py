from insights.projects.models import Project
from django.conf import settings


def get_tokens(project_uuid):
    try:
        project = Project.objects.get(uuid=project_uuid)
    except Project.DoesNotExist:
        return None

    if str(project.uuid) in settings.PROJECTS_VTEX:
        tokens = settings.PROJECT_TOKENS_VTEX.get(str(project_uuid))
        return tokens

    return None
