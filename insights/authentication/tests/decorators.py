import functools
from insights.projects.models import ProjectAuth


def with_project_auth(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        project = self.project
        user = self.user

        ProjectAuth.objects.create(project=project, user=user, role=1)

        return func(self, *args, **kwargs)

    return wrapper
